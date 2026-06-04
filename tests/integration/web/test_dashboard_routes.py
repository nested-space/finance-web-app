"""Integration tests for the dashboard + model API routes."""

from __future__ import annotations

import json

import pytest
from flask.testing import FlaskClient

pytestmark = pytest.mark.integration

_PAYLOAD_KEYS = {
    "year",
    "month",
    "labels",
    "finance_model",
    "income_outgoings",
    "budget_breakdown",
    "commitments_by_category",
    "insights",
}


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
    assert flask_client.get("/finance/api/model/2026/13").status_code == 404


def test_api_model_returns_documented_payload(flask_client: FlaskClient) -> None:
    _seed_month(flask_client)
    resp = flask_client.get("/finance/api/model/2026/6")
    assert resp.status_code == 200
    assert resp.is_json
    payload = resp.get_json()
    assert set(payload.keys()) == _PAYLOAD_KEYS
    assert payload["year"] == 2026 and payload["month"] == 6
    assert len(payload["labels"]) == 30
    # Monthly income of £2500 fires on the 15th.
    assert payload["income_outgoings"]["income"][14] == 2500.0
    # Closing balance is a JSON number.
    assert isinstance(payload["finance_model"]["balance"][-1], (int, float))


def test_api_expenses_curve_and_filter(flask_client: FlaskClient) -> None:
    _seed_month(flask_client)  # adds a GROCERIES budget of £200
    flask_client.post(
        "/finance/expenses",
        data={"name": "Food", "quantity": "50", "category": "GROCERIES", "date": "2026-06-05"},
    )
    resp = flask_client.get("/finance/api/expenses/2026/6")
    assert resp.status_code == 200
    data = resp.get_json()
    assert set(data.keys()) == {"labels", "spend_cumulative", "budget_cumulative"}
    assert len(data["labels"]) == 30
    assert data["spend_cumulative"][-1] == 50.0
    assert data["budget_cumulative"][-1] == 200.0

    # Filter to a category with no spend -> flat zero spend line.
    filtered = flask_client.get("/finance/api/expenses/2026/6?category=CLOTHING").get_json()
    assert filtered["spend_cumulative"][-1] == 0.0


def test_api_expenses_bad_month_and_category(flask_client: FlaskClient) -> None:
    assert flask_client.get("/finance/api/expenses/2026/13").status_code == 404
    assert flask_client.get("/finance/api/expenses/2026/6?category=NOPE").status_code == 400


def test_embedded_payload_matches_api(flask_client: FlaskClient) -> None:
    _seed_month(flask_client)
    page = flask_client.get("/finance/2026/6").data.decode()
    start = page.index('id="dashboard-data">') + len('id="dashboard-data">')
    end = page.index("</script>", start)
    embedded = json.loads(page[start:end])
    api = flask_client.get("/finance/api/model/2026/6").get_json()
    assert embedded == api
