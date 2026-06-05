"""Unit tests for budget item form parsing/validation."""

from __future__ import annotations

import pytest

from finance_web_app.core.contracts.errors import ValidationError
from finance_web_app.web.forms.budget_item_form import parse_budget_item_form

pytestmark = pytest.mark.unit


def _valid_form(**overrides: str) -> dict[str, str]:
    form = {"name": "Tesco", "category": "2"}
    form.update(overrides)
    return form


def test_valid_form_coerces() -> None:
    parsed = parse_budget_item_form(_valid_form())
    assert parsed.name == "Tesco"
    assert parsed.category_id == 2


def test_blank_name_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        parse_budget_item_form(_valid_form(name=" "))
    assert exc.value.field == "name"


@pytest.mark.parametrize("bad", ["", "GROCERIES", "0"])
def test_invalid_category_is_rejected(bad: str) -> None:
    with pytest.raises(ValidationError) as exc:
        parse_budget_item_form(_valid_form(category=bad))
    assert exc.value.field == "category"
