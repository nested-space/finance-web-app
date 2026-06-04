"""Landing page blueprint."""

from __future__ import annotations

from flask import Blueprint, redirect, url_for
from flask.typing import ResponseReturnValue

bp = Blueprint("home", __name__)


@bp.get("/")
def index() -> ResponseReturnValue:
    return redirect(url_for("summary.dashboard"))
