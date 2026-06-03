"""Unit tests for expense form parsing/validation."""

from __future__ import annotations

from datetime import date

import pytest

from finance_web_app.core.contracts.errors import ValidationError
from finance_web_app.domain.records import Category
from finance_web_app.web.forms.expense_form import parse_expense_form

pytestmark = pytest.mark.unit


def _valid_form(**overrides: str) -> dict[str, str]:
    form = {
        "name": "Lunch",
        "quantity": "5.50",
        "date": "2026-06-15",
        "category": "GROCERIES",
        "description": "sandwich",
    }
    form.update(overrides)
    return form


def test_valid_form_coerces_to_value_objects() -> None:
    parsed = parse_expense_form(_valid_form())
    assert parsed.name == "Lunch"
    assert parsed.quantity.pence() == 550
    assert parsed.category is Category.GROCERIES
    assert parsed.date == date(2026, 6, 15)
    assert parsed.description == "sandwich"


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


def test_unknown_category_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        parse_expense_form(_valid_form(category="GADGETS"))
    assert exc.value.field == "category"
