"""Integration tests for the web routes via the Flask test client.

The Flask client runs migrations on a fresh DB, which seeds the seven starter
categories (Groceries is id 2). Budgets and budget items reference a category id.
"""

from __future__ import annotations

import pytest
from flask.testing import FlaskClient

pytestmark = pytest.mark.integration

GROCERIES = "2"  # seeded starter category id

_VALID = {
    "quantity": "200.00",
    "category": GROCERIES,
    "effective_from": "2026-06-01",
}


def test_landing_page_redirects_to_dashboard(flask_client: FlaskClient) -> None:
    resp = flask_client.get("/")
    assert resp.status_code == 302
    assert "/finance" in resp.headers["Location"]


def test_budgets_page_starts_empty(flask_client: FlaskClient) -> None:
    resp = flask_client.get("/finance/budgets")
    assert resp.status_code == 200
    assert b"No budgets yet" in resp.data


def test_create_redirects_and_appears_in_listing(flask_client: FlaskClient) -> None:
    resp = flask_client.post("/finance/budgets", data=_VALID)
    assert resp.status_code == 302

    listing = flask_client.get("/finance/budgets")
    assert b"Groceries" in listing.data  # the category name
    assert b"200.00" in listing.data


def test_delete_removes_row(flask_client: FlaskClient) -> None:
    flask_client.post("/finance/budgets", data=_VALID)
    resp = flask_client.post("/finance/budgets/1/delete")
    assert resp.status_code == 302
    assert b"No budgets yet" in flask_client.get("/finance/budgets").data


def test_invalid_create_returns_400_with_message(flask_client: FlaskClient) -> None:
    resp = flask_client.post("/finance/budgets", data={"quantity": "x", "category": GROCERIES})
    assert resp.status_code == 400
    assert b"alert-danger" in resp.data


def test_manage_link_opens_budget_detail(flask_client: FlaskClient) -> None:
    flask_client.post("/finance/budgets", data=_VALID)
    listing = flask_client.get("/finance/budgets").data
    assert b"/finance/budgets/1" in listing  # the Manage link
    detail = flask_client.get("/finance/budgets/1")
    assert detail.status_code == 200
    assert b"Groceries budget" in detail.data


def test_budget_item_create_and_appears_on_detail(flask_client: FlaskClient) -> None:
    flask_client.post("/finance/budgets", data=_VALID)
    resp = flask_client.post("/finance/budgets/1/items", data={"name": "Tesco"})
    assert resp.status_code == 302
    assert b"Tesco" in flask_client.get("/finance/budgets/1").data


def test_budget_item_delete_removes_row(flask_client: FlaskClient) -> None:
    flask_client.post("/finance/budgets", data=_VALID)
    flask_client.post("/finance/budgets/1/items", data={"name": "Tesco"})
    assert flask_client.post("/finance/budgets/1/items/1/delete").status_code == 302
    assert b"No budget items yet" in flask_client.get("/finance/budgets/1").data


def test_budget_item_blank_name_returns_400(flask_client: FlaskClient) -> None:
    flask_client.post("/finance/budgets", data=_VALID)
    resp = flask_client.post("/finance/budgets/1/items", data={"name": "  "})
    assert resp.status_code == 400
    assert b"alert-danger" in resp.data


def test_detail_missing_budget_is_404(flask_client: FlaskClient) -> None:
    assert flask_client.get("/finance/budgets/999").status_code == 404


def test_charts_payload_is_embedded(flask_client: FlaskClient) -> None:
    flask_client.post("/finance/budgets", data=_VALID)
    page = flask_client.get("/finance/budgets").data
    assert b'id="budgets-charts"' in page
    assert b"chart-spend-vs-budget" in page
    assert b"chart-budget-history" in page


def test_unknown_url_renders_404(flask_client: FlaskClient) -> None:
    resp = flask_client.get("/no/such/page")
    assert resp.status_code == 404
    assert b"404" in resp.data


def test_delete_missing_id_renders_404(flask_client: FlaskClient) -> None:
    resp = flask_client.post("/finance/budgets/999/delete")
    assert resp.status_code == 404
