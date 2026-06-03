"""Web entry point.

Exposes ``create_app`` so the app can be launched with
``flask --app finance_web_app.web run``.
"""

from __future__ import annotations

from finance_web_app.core.runtime.app_factory import create_app

__all__ = ["create_app"]
