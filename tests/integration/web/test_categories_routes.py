"""Integration tests for the categories routes via the Flask test client.

The migration seeds seven starter categories (Groceries is id 2), so the page is
never empty and id 2 is a stable reference.
"""

from __future__ import annotations

import pytest
from flask.testing import FlaskClient

pytestmark = pytest.mark.integration

GROCERIES = "2"


def test_page_lists_seeded_categories(flask_client: FlaskClient) -> None:
    resp = flask_client.get("/finance/categories")
    assert resp.status_code == 200
    assert b"Groceries" in resp.data


def test_create_redirects_and_appears(flask_client: FlaskClient) -> None:
    resp = flask_client.post("/finance/categories", data={"name": "Holidays"})
    assert resp.status_code == 302
    assert b"Holidays" in flask_client.get("/finance/categories").data


def test_duplicate_name_returns_400(flask_client: FlaskClient) -> None:
    resp = flask_client.post("/finance/categories", data={"name": "Groceries"})
    assert resp.status_code == 400
    assert b"alert-danger" in resp.data


def test_delete_unused_category_removes_it(flask_client: FlaskClient) -> None:
    flask_client.post("/finance/categories", data={"name": "Holidays"})
    # The eighth category (Holidays) is unused -> deletable.
    resp = flask_client.post("/finance/categories/8/delete")
    assert resp.status_code == 302
    assert b"Holidays" not in flask_client.get("/finance/categories").data


def test_delete_in_use_category_returns_400(flask_client: FlaskClient) -> None:
    flask_client.post(
        "/finance/budgets",
        data={"quantity": "200", "category": GROCERIES, "effective_from": "2026-06-01"},
    )
    resp = flask_client.post(f"/finance/categories/{GROCERIES}/delete")
    assert resp.status_code == 400
    assert b"alert-danger" in resp.data
    # Still present after the blocked delete.
    assert b"Groceries" in flask_client.get("/finance/categories").data
