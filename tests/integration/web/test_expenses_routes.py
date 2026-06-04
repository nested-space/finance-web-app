"""Integration tests for the expenses routes via the Flask test client."""

from __future__ import annotations

import json
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


def test_api_expenses_returns_all_three_chart_shapes(flask_client: FlaskClient) -> None:
    today = date.today()
    resp = flask_client.get(
        f"/finance/api/expenses/{today.year}/{today.month}",
        headers={"Accept": "application/json"},
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert "current_month" in data
    assert "breakdown" in data
    assert "history" in data
    assert "labels" in data["current_month"]
    assert "spend_cumulative" in data["current_month"]
    assert "budget_cumulative" in data["current_month"]


def test_api_expenses_category_filter_excludes_other_categories(flask_client: FlaskClient) -> None:
    today = date.today()
    flask_client.post(
        "/finance/expenses",
        data={
            "name": "Bread",
            "quantity": "3.00",
            "date": today.isoformat(),
            "category": "GROCERIES",
            "description": "",
        },
    )
    flask_client.post(
        "/finance/expenses",
        data={
            "name": "Shoes",
            "quantity": "50.00",
            "date": today.isoformat(),
            "category": "CLOTHING",
            "description": "",
        },
    )
    resp = flask_client.get(
        f"/finance/api/expenses/{today.year}/{today.month}?category=GROCERIES",
        headers={"Accept": "application/json"},
    )
    data = json.loads(resp.data)
    assert data["breakdown"]["labels"] == ["Groceries"]
    assert len(data["breakdown"]["values"]) == 1
    assert data["current_month"]["spend_cumulative"][-1] == pytest.approx(3.0)
