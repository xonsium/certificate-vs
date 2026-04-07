import secrets
import string
from datetime import datetime, timezone
from typing import Any

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


CODE_ALPHABET = string.ascii_uppercase + string.digits


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Certificate(db.Model):
    __tablename__ = "certificates"

    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.String(64), nullable=False, index=True)
    verification_code = db.Column(db.String(6), nullable=False)
    name = db.Column(db.String(256), nullable=False)
    institution = db.Column(db.String(256), nullable=False)
    segment = db.Column(db.String(256), nullable=False)
    prize_place = db.Column(db.String(256), nullable=False)
    installment = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("event", "verification_code", name="uix_event_verification_code"),
        db.Index("idx_verification_code", "verification_code"),
    )


class Admin(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    api_token_hash = db.Column(db.String(256), nullable=True)
    api_token_created_at = db.Column(db.DateTime(timezone=True), nullable=True)


def _certificate_to_dict(cert: Certificate) -> dict[str, Any]:
    return {
        "_id": str(cert.id),
        "event": cert.event,
        "verification_code": cert.verification_code,
        "name": cert.name,
        "institution": cert.institution,
        "segment": cert.segment,
        "prize_place": cert.prize_place,
        "installment": cert.installment,
        "created_at": cert.created_at,
    }


def _admin_to_dict(admin: Admin) -> dict[str, Any]:
    return {
        "_id": str(admin.id),
        "username": admin.username,
        "password_hash": admin.password_hash,
        "api_token_hash": admin.api_token_hash,
        "api_token_created_at": admin.api_token_created_at,
    }


def generate_verification_code(length: int = 6) -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(length))


def generate_unique_code_for_event(event: str, max_attempts: int = 50) -> str:
    for _ in range(max_attempts):
        code = generate_verification_code()
        if not Certificate.query.filter_by(event=event, verification_code=code).first():
            return code
    raise RuntimeError("Could not generate a unique verification code.")


def certificate_create(data: dict[str, Any]) -> str:
    cert = Certificate(
        event=data["event"],
        verification_code=data["verification_code"].upper().strip(),
        name=data["name"].strip(),
        institution=data["institution"].strip(),
        segment=data["segment"].strip(),
        prize_place=data["prize_place"].strip(),
        installment=data["installment"].strip(),
        created_at=_now(),
    )
    db.session.add(cert)
    db.session.commit()
    return str(cert.id)


def certificate_create_with_optional_code(data: dict[str, Any]) -> str:
    payload = dict(data)
    code = (payload.get("verification_code") or "").strip()
    if not code:
        payload["verification_code"] = generate_unique_code_for_event(payload["event"])
    return certificate_create(payload)


def certificate_find_by_event_code(event: str, code: str) -> dict | None:
    cert = Certificate.query.filter_by(
        event=event,
        verification_code=code.upper().strip(),
    ).first()
    return _certificate_to_dict(cert) if cert else None


def certificate_get(oid: str) -> dict | None:
    try:
        cert_id = int(oid)
    except ValueError:
        return None
    cert = Certificate.query.get(cert_id)
    return _certificate_to_dict(cert) if cert else None


def certificate_update(oid: str, data: dict[str, Any]) -> dict | None:
    try:
        cert_id = int(oid)
    except ValueError:
        return None
    cert = Certificate.query.get(cert_id)
    if not cert:
        return None
    cert.event = data["event"]
    cert.verification_code = data["verification_code"].upper().strip()
    cert.name = data["name"].strip()
    cert.institution = data["institution"].strip()
    cert.segment = data["segment"].strip()
    cert.prize_place = data["prize_place"].strip()
    cert.installment = data["installment"].strip()
    db.session.commit()
    return _certificate_to_dict(cert)


def certificate_delete(oid: str) -> bool:
    try:
        cert_id = int(oid)
    except ValueError:
        return False
    cert = Certificate.query.get(cert_id)
    if not cert:
        return False
    db.session.delete(cert)
    db.session.commit()
    return True


def certificate_list_paginated(
    page: int,
    per_page: int,
    sort_field: str,
    sort_dir: int,
    search: str | None,
) -> tuple[list[dict], int]:
    query = Certificate.query
    if search and search.strip():
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Certificate.name.ilike(s),
                Certificate.institution.ilike(s),
                Certificate.verification_code.ilike(s),
            )
        )
    total = query.count()
    allowed_sort = {
        "created_at": Certificate.created_at,
        "event": Certificate.event,
        "name": Certificate.name,
        "verification_code": Certificate.verification_code,
    }
    sort_column = allowed_sort.get(sort_field, Certificate.created_at)
    sort_column = sort_column.desc() if sort_dir == -1 else sort_column.asc()
    rows = query.order_by(sort_column).offset((page - 1) * per_page).limit(per_page).all()
    return [_certificate_to_dict(row) for row in rows], total


def certificate_stats() -> dict[str, Any]:
    total = Certificate.query.count()
    counts = (
        db.session.query(Certificate.event, func.count(Certificate.id))
        .group_by(Certificate.event)
        .all()
    )
    by_event = {event: count for event, count in counts}
    return {"total": total, "by_event": by_event}


def admin_get_by_username(username: str) -> dict | None:
    admin = Admin.query.filter_by(username=username).first()
    return _admin_to_dict(admin) if admin else None


def admin_get_by_id(user_id: str) -> dict | None:
    try:
        admin_id = int(user_id)
    except ValueError:
        return None
    admin = Admin.query.get(admin_id)
    return _admin_to_dict(admin) if admin else None


def admin_create(username: str, password: str) -> str:
    admin = Admin(
        username=username.strip(),
        password_hash=generate_password_hash(password),
    )
    db.session.add(admin)
    db.session.commit()
    return str(admin.id)


def admin_set_password(user_id: str, new_password: str) -> bool:
    try:
        admin_id = int(user_id)
    except ValueError:
        return False
    admin = Admin.query.get(admin_id)
    if not admin:
        return False
    admin.password_hash = generate_password_hash(new_password)
    db.session.commit()
    return True


def verify_admin_password(admin_doc: dict, password: str) -> bool:
    return check_password_hash(admin_doc["password_hash"], password)


def generate_api_token() -> str:
    return "cvs_" + secrets.token_urlsafe(32)


def admin_set_api_token(user_id: str) -> str | None:
    try:
        admin_id = int(user_id)
    except ValueError:
        return None
    admin = Admin.query.get(admin_id)
    if not admin:
        return None
    token = generate_api_token()
    admin.api_token_hash = generate_password_hash(token)
    admin.api_token_created_at = _now()
    db.session.commit()
    return token


def admin_verify_api_token(token: str) -> dict | None:
    if not token:
        return None
    admins = Admin.query.filter(Admin.api_token_hash.isnot(None)).all()
    for admin in admins:
        if admin.api_token_hash and check_password_hash(admin.api_token_hash, token):
            return _admin_to_dict(admin)
    return None
