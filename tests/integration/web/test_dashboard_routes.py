"""Integration tests for the dashboard + model API routes."""

from __future__ import annotations

from datetime import date

import pytest
from flask.testing import FlaskClient

pytestmark = pytest.mark.integration


def _seed_month(client: FlaskClient) -> None:
    client.post(
        "/finance/income",
        data={
            "name": "Salary",
            "quantity": "2500",
            "recurrence": "MONTHLY",
            "effective_from": "2026-06-15",
        },
    )
    client.post(
        "/finance/budgets",
        data={
            "name": "Food",
            "quantity": "200",
            "category": "GROCERIES",
            "effective_from": "2026-06-01",
        },
    )


def test_dashboard_renders_with_embedded_payload(flask_client: FlaskClient) -> None:
    resp = flask_client.get("/finance")
    assert resp.status_code == 200
    assert b'id="dashboard-data"' in resp.data
    assert b"Insights" in resp.data
    assert b"chart-finance-model" in resp.data


def test_dashboard_deep_link_for_month(flask_client: FlaskClient) -> None:
    _seed_month(flask_client)
    resp = flask_client.get("/finance/2026/6")
    assert resp.status_code == 200
    assert b"June 2026" in resp.data


def test_bad_month_is_404(flask_client: FlaskClient) -> None:
    assert flask_client.get("/finance/2026/13").status_code == 404


def test_future_month_redirects_to_dashboard(flask_client: FlaskClient) -> None:
    today = date.today()
    future_year, future_month = (today.year + 1, today.month)
    resp = flask_client.get(f"/finance/{future_year}/{future_month}")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/finance")


def test_current_month_disables_home_and_next(flask_client: FlaskClient) -> None:
    resp = flask_client.get("/finance")
    assert resp.status_code == 200
    # Home and Next both stay in the DOM but are disabled; Prev stays active.
    assert b'id="nav-home"' in resp.data
    assert b'id="nav-next"' in resp.data
    assert b'id="nav-prev"' in resp.data
    # Exactly the two forward links (home + next) are disabled, not Prev.
    assert resp.data.count(b'aria-disabled="true"') == 2


def test_dashboard_has_home_button(flask_client: FlaskClient) -> None:
    resp = flask_client.get("/finance")
    assert resp.status_code == 200
    assert b'id="nav-home"' in resp.data
    assert b'href="/finance"' in resp.data


def test_past_month_enables_home_and_next(flask_client: FlaskClient) -> None:
    today = date.today()
    past_year, past_month = (today.year - 1, today.month)
    resp = flask_client.get(f"/finance/{past_year}/{past_month}")
    assert resp.status_code == 200
    assert b'id="nav-next"' in resp.data
    assert b"is-disabled" not in resp.data
    assert b"aria-disabled" not in resp.data


def test_api_expenses_curve_and_filter(flask_client: FlaskClient) -> None:
    _seed_month(flask_client)  # adds a GROCERIES budget of £200
    flask_client.post(
        "/finance/expenses",
        data={"name": "Food", "quantity": "50", "category": "GROCERIES", "date": "2026-06-05"},
    )
    resp = flask_client.get("/finance/api/expenses/2026/6")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "current_month" in data and "breakdown" in data and "history" in data
    assert len(data["current_month"]["labels"]) == 30
    assert data["current_month"]["spend_cumulative"][-1] == 50.0
    assert data["current_month"]["budget_cumulative"][-1] == 200.0

    # Filter to a category with no spend -> flat zero spend line.
    filtered = flask_client.get("/finance/api/expenses/2026/6?category=CLOTHING").get_json()
    assert filtered["current_month"]["spend_cumulative"][-1] == 0.0


def test_api_expenses_bad_month_and_category(flask_client: FlaskClient) -> None:
    assert flask_client.get("/finance/api/expenses/2026/13").status_code == 404
    assert flask_client.get("/finance/api/expenses/2026/6?category=NOPE").status_code == 400
