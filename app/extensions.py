from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy

csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = "admin.login"
login_manager.login_message_category = "error"
db = SQLAlchemy()


def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        _ensure_default_admin(app)
    return db


def _ensure_default_admin(app):
    from app import models as m

    username = app.config["DEFAULT_ADMIN_USERNAME"]
    password = app.config["DEFAULT_ADMIN_PASSWORD"]
    try:
        if m.admin_get_by_username(username):
            return
        m.admin_create(username, password)
        app.logger.info(
            "Created default admin %r — change password under Admin → Settings.",
            username,
        )
    except Exception as exc:
        app.logger.warning("Could not ensure default admin user: %s", exc)
