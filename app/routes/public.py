from flask import Blueprint, render_template

from app.config import Config

bp = Blueprint("public", __name__)


@bp.route("/")
def index():
    return render_template("index.html", events=Config.EVENTS)
