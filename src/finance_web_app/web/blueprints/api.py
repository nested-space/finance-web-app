"""JSON API for post-paint refetches.

Returns data already shaped by services — no business logic here. Currently the
dashboard's per-month payload, used by the dashboard JS on month navigation
(``docs/ARCHITECTURE.md`` -> "Frontend data delivery").
"""

from __future__ import annotations

from flask import Blueprint, abort, jsonify
from flask.typing import ResponseReturnValue

from finance_web_app.web.blueprints.summary import build_dashboard_payload

bp = Blueprint("api", __name__, url_prefix="/finance/api")


@bp.get("/model/<int:year>/<int:month>")
def model(year: int, month: int) -> ResponseReturnValue:
    if not 1 <= month <= 12:
        abort(404)
    return jsonify(build_dashboard_payload(year, month))
