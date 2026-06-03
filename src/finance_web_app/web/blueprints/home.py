"""Landing page blueprint."""

from __future__ import annotations

from flask import Blueprint, render_template

bp = Blueprint("home", __name__)


@bp.get("/")
def index() -> str:
    return render_template("index.html")
