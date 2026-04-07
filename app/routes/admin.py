from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from app.auth import AdminUser
from app.config import Config
from app.forms import CertificateForm, ChangePasswordForm, GenerateApiTokenForm, LoginForm
from app import models as m

bp = Blueprint("admin", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        doc = m.admin_get_by_username(form.username.data)
        if doc and m.verify_admin_password(doc, form.password.data):
            login_user(AdminUser(doc), remember=True)
            next_url = request.args.get("next") or url_for("admin.dashboard")
            return redirect(next_url)
        flash("Invalid username or password.", "error")

    return render_template("admin/login.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("admin.login"))


@bp.route("/")
@login_required
def dashboard():
    page = max(1, request.args.get("page", 1, type=int))
    sort = request.args.get("sort", "created_at")
    order = request.args.get("order", "desc")
    search = request.args.get("q", "", type=str)
    sort_dir = -1 if order == "desc" else 1

    rows, total = m.certificate_list_paginated(
        page=page,
        per_page=Config.PER_PAGE,
        sort_field=sort,
        sort_dir=sort_dir,
        search=search or None,
    )
    stats = m.certificate_stats()
    pages = (total + Config.PER_PAGE - 1) // Config.PER_PAGE if total else 1

    return render_template(
        "admin/dashboard.html",
        rows=rows,
        page=page,
        pages=pages,
        total=total,
        sort=sort,
        order=order,
        q=search or "",
        stats=stats,
        events=Config.EVENTS,
    )


@bp.route("/certificates/new", methods=["GET", "POST"])
@login_required
def certificate_new():
    form = CertificateForm()
    if form.validate_on_submit():
        code = (form.verification_code.data or "").strip()
        if not code:
            try:
                code = m.generate_unique_code_for_event(form.event.data)
            except RuntimeError as e:
                flash(str(e), "error")
                return render_template("admin/certificate_form.html", form=form, edit=False)
        else:
            code = code.upper()
        data = {
            "event": form.event.data,
            "verification_code": code,
            "name": form.name.data,
            "institution": form.institution.data,
            "segment": form.segment.data,
            "prize_place": form.prize_place.data,
            "installment": form.installment.data,
        }
        try:
            oid = m.certificate_create(data)
            flash("Certificate record created.", "success")
            return redirect(url_for("admin.certificate_edit", oid=oid))
        except IntegrityError:
            flash(
                "A record with this event and verification code already exists.",
                "error",
            )
        except Exception as exc:
            flash(f"Could not save: {exc}", "error")

    return render_template("admin/certificate_form.html", form=form, edit=False)


@bp.route("/certificates/<oid>/edit", methods=["GET", "POST"])
@login_required
def certificate_edit(oid):
    doc = m.certificate_get(oid)
    if not doc:
        flash("Record not found.", "error")
        return redirect(url_for("admin.dashboard"))

    form = CertificateForm()
    if request.method == "GET":
        form.event.data = doc.get("event")
        form.verification_code.data = doc.get("verification_code", "")
        form.name.data = doc.get("name", "")
        form.institution.data = doc.get("institution", "")
        form.segment.data = doc.get("segment", "")
        form.prize_place.data = doc.get("prize_place", "")
        form.installment.data = doc.get("installment", "")

    if form.validate_on_submit():
        code = (form.verification_code.data or "").strip().upper()
        if not code:
            flash("Verification code is required when editing.", "error")
            return render_template("admin/certificate_form.html", form=form, edit=True, oid=oid)
        data = {
            "event": form.event.data,
            "verification_code": code,
            "name": form.name.data,
            "institution": form.institution.data,
            "segment": form.segment.data,
            "prize_place": form.prize_place.data,
            "installment": form.installment.data,
        }
        try:
            updated = m.certificate_update(oid, data)
            if updated:
                flash("Record updated.", "success")
                return redirect(url_for("admin.certificate_edit", oid=oid))
        except IntegrityError:
            flash(
                "Another record already uses this event and verification code.",
                "error",
            )
        except Exception as exc:
            flash(f"Could not update: {exc}", "error")

    return render_template("admin/certificate_form.html", form=form, edit=True, oid=oid)


@bp.route("/certificates/<oid>/delete", methods=["POST"])
@login_required
def certificate_delete(oid):
    if m.certificate_delete(oid):
        flash("Record deleted.", "success")
    else:
        flash("Could not delete record.", "error")
    return redirect(url_for("admin.dashboard"))


@bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    form = ChangePasswordForm()
    token_form = GenerateApiTokenForm()

    if form.submit.data and form.validate_on_submit():
        doc = m.admin_get_by_id(current_user.id)
        if not doc or not m.verify_admin_password(doc, form.current_password.data):
            flash("Current password is incorrect.", "error")
        elif m.admin_set_password(current_user.id, form.new_password.data):
            flash("Password updated.", "success")
            return redirect(url_for("admin.settings"))
        else:
            flash("Could not update password.", "error")
    elif token_form.generate_token.data and token_form.validate_on_submit():
        token = m.admin_set_api_token(current_user.id)
        if token:
            flash(
                f"API token generated. Copy it now: {token}",
                "success",
            )
            return redirect(url_for("admin.settings"))
        flash("Could not generate API token.", "error")

    return render_template("admin/settings.html", form=form, token_form=token_form)
