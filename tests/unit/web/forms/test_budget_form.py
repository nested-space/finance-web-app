"""Unit tests for budget form parsing/validation."""

from __future__ import annotations

from datetime import date

import pytest

from finance_web_app.core.contracts.errors import ValidationError
from finance_web_app.domain.records import Category
from finance_web_app.web.forms.budget_form import parse_budget_form

pytestmark = pytest.mark.unit


def _valid_form(**overrides: str) -> dict[str, str]:
    form = {
        "name": "Groceries",
        "quantity": "200.00",
        "category": "GROCERIES",
        "effective_from": "2026-06-01",
        "effective_stop": "",
    }
    form.update(overrides)
    return form


def test_valid_form_coerces_to_value_objects() -> None:
    parsed = parse_budget_form(_valid_form())
    assert parsed.name == "Groceries"
    assert parsed.quantity.pence() == 20000
    assert parsed.category is Category.GROCERIES
    assert parsed.period.from_date == date(2026, 6, 1)
    assert parsed.period.stop_date is None


def test_missing_effective_from_defaults_to_today() -> None:
    parsed = parse_budget_form(_valid_form(effective_from=""))
    assert parsed.period.from_date == date.today()


def test_missing_name_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        parse_budget_form(_valid_form(name="  "))
    assert exc.value.field == "name"


@pytest.mark.parametrize("bad", ["", "abc", "-5"])
def test_bad_quantity_is_rejected(bad: str) -> None:
    with pytest.raises(ValidationError) as exc:
        parse_budget_form(_valid_form(quantity=bad))
    assert exc.value.field == "quantity"


def test_unknown_category_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        parse_budget_form(_valid_form(category="GADGETS"))
    assert exc.value.field == "category"


def test_stop_before_from_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        parse_budget_form(_valid_form(effective_from="2026-06-10", effective_stop="2026-06-01"))
    assert exc.value.field == "effective_stop"


def test_malformed_date_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        parse_budget_form(_valid_form(effective_from="06/01/2026"))
    assert exc.value.field == "effective_from"
