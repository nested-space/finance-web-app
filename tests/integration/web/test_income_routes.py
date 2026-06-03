"""Integration tests for the income routes via the Flask test client."""

from __future__ import annotations

import pytest
from flask.testing import FlaskClient

pytestmark = pytest.mark.integration


def _valid() -> dict[str, str]:
    return {
        "name": "Salary",
        "quantity": "2500.00",
        "recurrence": "QUARTERLY",
        "effective_from": "2026-01-01",
    }


def test_page_starts_empty(flask_client: FlaskClient) -> None:
    resp = flask_client.get("/finance/income")
    assert resp.status_code == 200
    assert b"No income streams yet" in resp.data


def test_create_redirects_and_appears(flask_client: FlaskClient) -> None:
    assert flask_client.post("/finance/income", data=_valid()).status_code == 302
    listing = flask_client.get("/finance/income").data
    assert b"Salary" in listing
    assert b"Quarterly" in listing


def test_delete_removes(flask_client: FlaskClient) -> None:
    flask_client.post("/finance/income", data=_valid())
    assert flask_client.post("/finance/income/1/delete").status_code == 302
    assert b"No income streams yet" in flask_client.get("/finance/income").data


def test_stop_before_from_returns_400(flask_client: FlaskClient) -> None:
    resp = flask_client.post("/finance/income", data=_valid() | {"effective_stop": "2025-01-01"})
    assert resp.status_code == 400
    assert b"alert-danger" in resp.data
