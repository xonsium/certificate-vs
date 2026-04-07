import re

from flask import Blueprint, jsonify, request
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
    if not re.match(r"^[A-Za-z0-9]{6}$", code):
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

    if event not in Config.EVENTS:
        return jsonify({"ok": False, "error": "invalid_event"}), 400
    if code and not re.match(r"^[A-Za-z0-9]{6}$", code):
        return jsonify({"ok": False, "error": "invalid_code"}), 400
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
