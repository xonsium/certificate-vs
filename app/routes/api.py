import re
from flask import Blueprint, jsonify, request, render_template
from flask_wtf.csrf import CSRFError, validate_csrf
from sqlalchemy.exc import IntegrityError

from app.config import Config
from app import models as m
from app.extensions import csrf


bp = Blueprint("api", __name__)


def _read_api_token() -> str:
    auth = (request.headers.get("Authorization") or "").strip()
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return (request.headers.get("X-API-Token") or "").strip()


@bp.route("/verify", methods=["POST"])
def verify():
    token = request.headers.get("X-CSRFToken") or request.headers.get("X-CSRF-Token")
    try:
        validate_csrf(token)
    except CSRFError:
        return jsonify({"ok": False, "error": "invalid_csrf"}), 403

    if not request.is_json:
        return jsonify({"ok": False, "error": "expected_json"}), 400

    data = request.get_json(silent=True) or {}
    event = (data.get("event") or "").strip()
    code = (data.get("code") or "").strip()

    if event not in Config.EVENTS:
        return jsonify({"ok": False, "error": "invalid_event"}), 400
    if not re.match(r"^[A-Za-z0-9]{6,64}$", code):
        return jsonify({"ok": False, "error": "invalid_code"}), 400

    doc = m.certificate_find_by_event_code(event, code)
    if not doc:
        return jsonify({"ok": False, "error": "not_found"}), 404

    return jsonify(
        {
            "ok": True,
            "certificate": {
                "event": doc["event"],
                "name": doc["name"],
                "institution": doc["institution"],
                "segment": doc["segment"],
                "prize_place": doc["prize_place"],
                "installment": doc["installment"],
            },
        }
    )


@bp.route("/certificates", methods=["POST"])
@csrf.exempt
def certificates_create():
    token = _read_api_token()
    admin_doc = m.admin_verify_api_token(token)
    if not admin_doc:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    if not request.is_json:
        return jsonify({"ok": False, "error": "expected_json"}), 400

    data = request.get_json(silent=True) or {}
    event = (data.get("event") or "").strip()
    code = (data.get("verification_code") or "").strip().upper()
    name = (data.get("name") or "").strip()
    institution = (data.get("institution") or "").strip()
    segment = (data.get("segment") or "").strip()
    prize_place = (data.get("prize_place") or "").strip()
    installment = (data.get("installment") or "").strip()
    cert_type = (data.get("cert_type") or "winner").strip().lower()

    if event not in Config.EVENTS:
        return jsonify({"ok": False, "error": "invalid_event"}), 400
    if code and not re.match(r"^[A-Za-z0-9]{64}$", code):
        return jsonify({"ok": False, "error": "invalid_code"}), 400
    
    # Validate cert_type
    if cert_type not in ["winner", "participation"]:
        return jsonify({"ok": False, "error": "invalid_cert_type"}), 400

    # For participation certificates, only event, code, and installment are required
    if cert_type == "participation" and event == "FTMPC":
        if not installment:
            return jsonify({"ok": False, "error": "missing_fields", "fields": ["installment"]}), 400
        # Participation certs don't need the other fields
        required = {
            "name": name,
            "institution": institution,
            "prize_place": prize_place,
            "installment": installment,
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            return jsonify({"ok": False, "error": "missing_fields", "fields": missing}), 400
    else:
        # For winner certificates, all fields are required
        required = {
            "name": name,
            "institution": institution,
            "segment": segment,
            "prize_place": prize_place,
            "installment": installment,
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            return jsonify({"ok": False, "error": "missing_fields", "fields": missing}), 400

    payload = {
        "event": event,
        "verification_code": code,
        "name": name,
        "institution": institution,
        "segment": segment,
        "prize_place": prize_place,
        "installment": installment,
        "cert_type": cert_type,
    }
    try:
        oid = m.certificate_create_with_optional_code(payload)
    except IntegrityError:
        return jsonify({"ok": False, "error": "duplicate_event_code"}), 409
    except RuntimeError as exc:
        return jsonify({"ok": False, "error": "code_generation_failed", "message": str(exc)}), 500

    created = m.certificate_get(oid)
    return jsonify(
        {
            "ok": True,
            "id": oid,
            "certificate": {
                "event": created["event"],
                "verification_code": created["verification_code"],
                "name": created["name"],
                "institution": created["institution"],
                "segment": created["segment"],
                "prize_place": created["prize_place"],
                "installment": created["installment"],
            },
            "created_by": admin_doc.get("username"),
        }
    ), 201


@bp.route("/download-certificate", methods=["POST"])
def download_certificate():
    """Generate and return certificate HTML for PDF generation via html2canvas."""
    token = request.headers.get("X-CSRFToken") or request.headers.get("X-CSRF-Token")
    try:
        validate_csrf(token)
    except CSRFError:
        return jsonify({"ok": False, "error": "invalid_csrf"}), 403

    if not request.is_json:
        return jsonify({"ok": False, "error": "expected_json"}), 400

    data = request.get_json(silent=True) or {}
    event = (data.get("event") or "").strip()
    code = (data.get("code") or "").strip().upper()
    cert_type = (data.get("cert_type") or "winner").strip()

    if event not in Config.EVENTS:
        return jsonify({"ok": False, "error": "invalid_event"}), 400

    # For participation certificates without code, skip verification
    if cert_type == "participation" and not code:
        # Generate participation certificate directly
        try:
            # Get installment from request or default to "1"
            installment = (data.get("installment") or "1").strip()
            
            template_path = _get_participation_template_path(event, installment)
            if not template_path:
                return jsonify({"ok": False, "error": "invalid_event"}), 400

            # For FTMPC participation, we need to look up the participant data
            # by event (since all FTMPC participants have codes)
            name = ""
            institution = ""
            segment = ""
            prize_place = ""
            code = ""

            # If FTMPC, we need to find a participant record to get the data
            if event == "FTMPC":
                # Find any FTMPC participant to get template data
                participant = m.certificate_find_first_by_event(event)
                if participant:
                    name = participant.get("name", "")
                    institution = participant.get("institution", "")
                    segment = participant.get("segment", "")
                    prize_place = participant.get("prize_place", "")
                    code = participant.get("verification_code", "")

            html_string = render_template(
                "certificate_pdf.html",
                certificate_template=template_path,
                event=event,
                name=name,
                institution=institution,
                segment=segment,
                prize_place=prize_place,
                installment=installment,
                code=code,
            )

            return jsonify({
                "ok": True,
                "html": html_string,
                "filename": f"{event}_participation_{installment}",
            })
        except Exception as e:
            return jsonify({"ok": False, "error": "html_generation_failed", "message": str(e)}), 500

    # For winner certificates or FTMPC participation, require verification code
    if not re.match(r"^[A-Za-z0-9]{64}$", code):
        return jsonify({"ok": False, "error": "invalid_code"}), 400

    doc = m.certificate_find_by_event_code(event, code)
    if not doc:
        return jsonify({"ok": False, "error": "not_found"}), 404

    # Map event + installment to template file
    template_path_map = {
        ("FTMPC", "1"): "certificates/ftmpc_1.html",
        ("FTMPC", "2"): "certificates/ftmpc_2.html",
        ("INIT", "1"): "certificates/init_1.html",
        ("INIT", "2"): "certificates/init_2.html",
        ("Thynk", "1"): "certificates/thynk_1.html",
        ("Thynk", "2"): "certificates/thynk_2.html",
        ("PixelCon", "1"): "certificates/pixelcon_1.html",
        ("PixelCon", "2"): "certificates/pixelcon_2.html",
    }
    # Fallback to event-based template if installment-specific not found
    fallback_map = {
        "FTMPC": "certificates/ftmpc.html",
        "INIT": "certificates/init.html",
        "Thynk": "certificates/thynk.html",
        "PixelCon": "certificates/pixelcon.html",
    }
    installment = doc.get("installment", "1")
    template_path = template_path_map.get((event, installment))
    if not template_path:
        template_path = fallback_map.get(event)
    if not template_path:
        return jsonify({"ok": False, "error": "invalid_event"}), 400

    try:
        # Render the certificate template with certificate data
        html_string = render_template(
            "certificate_pdf.html",
            certificate_template=template_path,
            event=event,
            name=doc["name"],
            institution=doc["institution"],
            segment=doc["segment"],
            prize_place=doc["prize_place"],
            installment=doc["installment"],
            code=doc["verification_code"],
        )

        return jsonify({
            "ok": True,
            "html": html_string,
            "filename": f"{event}_{doc['installment']}_{code}",
        })
    except Exception as e:
        return jsonify({"ok": False, "error": "html_generation_failed", "message": str(e)}), 500


def _get_participation_template_path(event: str, installment: str) -> str | None:
    """Get the template path for participation certificates."""
    participation_template_map = {
        ("FTMPC", "1"): "certificates/ftmpc_participation_1.html",
        ("FTMPC", "2"): "certificates/ftmpc_participation_2.html",
        ("INIT", "1"): "certificates/init_participation_1.html",
        ("INIT", "2"): "certificates/init_participation_2.html",
        ("Thynk", "1"): "certificates/thynk_participation_1.html",
        ("Thynk", "2"): "certificates/thynk_participation_2.html",
        ("PixelCon", "1"): "certificates/pixelcon_participation_1.html",
        ("PixelCon", "2"): "certificates/pixelcon_participation_2.html",
    }
    # Fallback to event-based participation template
    participation_fallback_map = {
        "FTMPC": "certificates/ftmpc_participation.html",
        "INIT": "certificates/init_participation.html",
        "Thynk": "certificates/thynk_participation.html",
        "PixelCon": "certificates/pixelcon_participation.html",
    }
    template_path = participation_template_map.get((event, installment))
    if not template_path:
        template_path = participation_fallback_map.get(event)
    return template_path
