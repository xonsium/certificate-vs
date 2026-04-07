from flask import Flask

from app.config import Config
from app.extensions import csrf, init_db, login_manager
from app.auth import load_user


def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
        static_url_path="/static",
    )
    app.config.from_object(config_class)

    init_db(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.user_loader(load_user)

    from app.routes.public import bp as public_bp
    from app.routes.api import bp as api_bp
    from app.routes.admin import bp as admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    return app
