"""Integration tests for the expenses routes via the Flask test client."""

from __future__ import annotations

from datetime import date

import pytest
from flask.testing import FlaskClient

pytestmark = pytest.mark.integration


def _valid() -> dict[str, str]:
    return {
        "name": "Lunch",
        "quantity": "5.50",
        "date": date.today().isoformat(),
        "category": "GROCERIES",
        "description": "sandwich",
    }


def test_page_starts_empty(flask_client: FlaskClient) -> None:
    resp = flask_client.get("/finance/expenses")
    assert resp.status_code == 200
    assert b"No expenses this month" in resp.data


def test_create_redirects_and_appears(flask_client: FlaskClient) -> None:
    assert flask_client.post("/finance/expenses", data=_valid()).status_code == 302
    listing = flask_client.get("/finance/expenses")
    assert b"Lunch" in listing.data
    assert b"5.50" in listing.data


def test_delete_removes_row(flask_client: FlaskClient) -> None:
    flask_client.post("/finance/expenses", data=_valid())
    assert flask_client.post("/finance/expenses/1/delete").status_code == 302
    assert b"No expenses this month" in flask_client.get("/finance/expenses").data


def test_charts_payload_is_embedded(flask_client: FlaskClient) -> None:
    flask_client.post("/finance/expenses", data=_valid())
    page = flask_client.get("/finance/expenses").data
    assert b'id="expenses-charts"' in page
    assert b"chart-expense-curve" in page
    assert b"expense-category-filter" in page


def test_invalid_create_returns_400(flask_client: FlaskClient) -> None:
    resp = flask_client.post(
        "/finance/expenses", data={"name": "", "quantity": "x", "category": "GROCERIES"}
    )
    assert resp.status_code == 400
    assert b"alert-danger" in resp.data
