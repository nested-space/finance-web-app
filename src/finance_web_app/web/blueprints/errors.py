"""Error-to-HTTP mapping.

Typed domain errors and unmatched routes render the 404 page; no stack trace
reaches the user (``docs/DEVELOPMENT.md`` -> "Security baseline").
"""

from __future__ import annotations

from flask import Flask, render_template
from flask.typing import ResponseReturnValue

from finance_web_app.core.contracts.errors import NotFoundError


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def handle_404(_error: object) -> ResponseReturnValue:
        return render_template("404.html"), 404

    @app.errorhandler(NotFoundError)
    def handle_not_found(_error: NotFoundError) -> ResponseReturnValue:
        return render_template("404.html"), 404
