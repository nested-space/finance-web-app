"""Application factory.

Builds the Flask app: resolves configuration from the environment, applies
pending Alembic migrations, creates the SQLAlchemy engine, wires the
request-scoped session lifecycle, registers blueprints and error handlers, and
installs request logging that records outcomes but never payloads
(``docs/OPERATIONS.md`` -> "Environment variables", "Schema and migrations",
"Observability").
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from flask import Flask, Response, g, request

from finance_web_app.core.runtime.container import close_session
from finance_web_app.infrastructure.persistence.engine import make_engine
from finance_web_app.infrastructure.persistence.migrate import upgrade_to_head

DEFAULT_DB_PATH = "./data/finance.db"

_logger = logging.getLogger("finance_web_app")


def create_app(db_path: str | None = None) -> Flask:
    _configure_logging()

    app = Flask("finance_web_app.web", template_folder="templates", static_folder="static")
    resolved_db = db_path or os.environ.get("FINANCE_DB_PATH", DEFAULT_DB_PATH)
    if resolved_db != ":memory:":
        Path(resolved_db).parent.mkdir(parents=True, exist_ok=True)

    upgrade_to_head(resolved_db)
    app.config["DB_ENGINE"] = make_engine(resolved_db)

    app.teardown_appcontext(close_session)
    _register_request_logging(app)

    # Imported here, not at module top, so importing this module does not pull in
    # the web package (whose __init__ re-exports create_app) -- a circular import.
    from finance_web_app.web.blueprints import budgets, home
    from finance_web_app.web.blueprints.errors import register_error_handlers

    app.register_blueprint(home.bp)
    app.register_blueprint(budgets.bp)
    register_error_handlers(app)

    return app


def _configure_logging() -> None:
    level_name = os.environ.get("FINANCE_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(level=level)


def _register_request_logging(app: Flask) -> None:
    @app.before_request
    def _start_timer() -> None:
        g.request_start = time.perf_counter()

    @app.after_request
    def _log_request(response: Response) -> Response:
        start = g.pop("request_start", None)
        duration_ms = (time.perf_counter() - start) * 1000 if start is not None else 0.0
        _logger.info(
            "%s %s %s %.1fms",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )
        return response
