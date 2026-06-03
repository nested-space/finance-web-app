"""Programmatic Alembic runner.

Runs ``alembic upgrade head`` against a target database without depending on the
process working directory or ``alembic.ini`` -- the script location is resolved
from the installed package so it works for a deployed app too. A migration
failure propagates, so startup aborts loudly (``docs/OPERATIONS.md`` -> "Schema
and migrations").
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

import finance_web_app
from finance_web_app.infrastructure.persistence.engine import database_url

_MIGRATIONS_DIR = Path(finance_web_app.__file__).resolve().parent / "migrations"


def _config(db_path: str) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(_MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", database_url(db_path))
    return cfg


def upgrade_to_head(db_path: str) -> None:
    command.upgrade(_config(db_path), "head")
