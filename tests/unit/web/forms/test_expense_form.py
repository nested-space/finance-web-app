"""Unit tests for expense form parsing/validation."""

from __future__ import annotations

from datetime import date

import pytest

from finance_web_app.core.contracts.errors import ValidationError
from finance_web_app.web.forms.expense_form import parse_expense_form

pytestmark = pytest.mark.unit


def _valid_form(**overrides: str) -> dict[str, str]:
    form = {
        "name": "Lunch",
        "quantity": "5.50",
        "date": "2026-06-15",
        "category": "2",
        "budget_item": "",
        "description": "sandwich",
    }
    form.update(overrides)
    return form


def test_valid_form_coerces_to_value_objects() -> None:
    parsed = parse_expense_form(_valid_form())
    assert parsed.name == "Lunch"
    assert parsed.quantity.pence() == 550
    assert parsed.category_id == 2
    assert parsed.budget_item_id is None
    assert parsed.date == date(2026, 6, 15)
    assert parsed.description == "sandwich"


def test_budget_item_is_parsed_when_present() -> None:
    assert parse_expense_form(_valid_form(budget_item="7")).budget_item_id == 7


def test_blank_description_becomes_none() -> None:
    assert parse_expense_form(_valid_form(description="  ")).description is None


def test_missing_name_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        parse_expense_form(_valid_form(name=" "))
    assert exc.value.field == "name"


@pytest.mark.parametrize("bad", ["", "abc", "-5"])
def test_bad_quantity_is_rejected(bad: str) -> None:
    with pytest.raises(ValidationError) as exc:
        parse_expense_form(_valid_form(quantity=bad))
    assert exc.value.field == "quantity"


def test_missing_date_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        parse_expense_form(_valid_form(date=""))
    assert exc.value.field == "date"


@pytest.mark.parametrize("bad", ["", "GROCERIES", "0"])
def test_invalid_category_is_rejected(bad: str) -> None:
    with pytest.raises(ValidationError) as exc:
        parse_expense_form(_valid_form(category=bad))
    assert exc.value.field == "category"


@pytest.mark.parametrize("bad", ["abc", "0", "-1"])
def test_invalid_budget_item_is_rejected(bad: str) -> None:
    with pytest.raises(ValidationError) as exc:
        parse_expense_form(_valid_form(budget_item=bad))
    assert exc.value.field == "budget_item"
