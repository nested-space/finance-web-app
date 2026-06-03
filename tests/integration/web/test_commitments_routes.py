"""Integration tests for the commitments routes via the Flask test client."""

from __future__ import annotations

import pytest
from flask.testing import FlaskClient

pytestmark = pytest.mark.integration


def _valid() -> dict[str, str]:
    return {
        "name": "Netflix",
        "quantity": "9.99",
        "category": "ENTERTAINMENT",
        "recurrence": "MONTHLY",
        "effective_from": "2026-01-15",
        "length": "6",
        "length_unit": "MONTHS",
    }


def test_page_starts_empty(flask_client: FlaskClient) -> None:
    resp = flask_client.get("/finance/commitments")
    assert resp.status_code == 200
    assert b"No commitments yet" in resp.data


def test_create_redirects_and_groups_by_recurrence(flask_client: FlaskClient) -> None:
    assert flask_client.post("/finance/commitments", data=_valid()).status_code == 302
    listing = flask_client.get("/finance/commitments").data
    assert b"Netflix" in listing
    assert b"Monthly" in listing  # the recurrence group heading


def test_once_only_creates_without_length(flask_client: FlaskClient) -> None:
    resp = flask_client.post(
        "/finance/commitments",
        data={
            "name": "Setup",
            "quantity": "50",
            "category": "KIDS",
            "recurrence": "ONCE_ONLY",
            "effective_from": "2026-03-15",
        },
    )
    assert resp.status_code == 302


def test_delete_removes(flask_client: FlaskClient) -> None:
    flask_client.post("/finance/commitments", data=_valid())
    assert flask_client.post("/finance/commitments/1/delete").status_code == 302
    assert b"No commitments yet" in flask_client.get("/finance/commitments").data


def test_category_outside_subset_returns_400(flask_client: FlaskClient) -> None:
    resp = flask_client.post("/finance/commitments", data=_valid() | {"category": "PETROL"})
    assert resp.status_code == 400
    assert b"alert-danger" in resp.data
