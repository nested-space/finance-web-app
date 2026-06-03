"""Unit tests for income form parsing/validation."""

from __future__ import annotations

from datetime import date

import pytest

from finance_web_app.core.contracts.errors import ValidationError
from finance_web_app.domain.recurrence import Recurrence
from finance_web_app.web.forms.income_form import parse_income_form

pytestmark = pytest.mark.unit


def _valid_form(**overrides: str) -> dict[str, str]:
    form = {
        "name": "Salary",
        "quantity": "2500.00",
        "recurrence": "QUARTERLY",
        "effective_from": "2026-01-01",
        "effective_stop": "",
    }
    form.update(overrides)
    return form


def test_valid_form_allows_quarterly_and_open_ended_stop() -> None:
    parsed = parse_income_form(_valid_form())
    assert parsed.recurrence is Recurrence.QUARTERLY
    assert parsed.effective_from == date(2026, 1, 1)
    assert parsed.effective_stop is None


def test_effective_stop_is_parsed_when_given() -> None:
    parsed = parse_income_form(_valid_form(effective_stop="2026-12-31"))
    assert parsed.effective_stop == date(2026, 12, 31)


def test_stop_before_from_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        parse_income_form(_valid_form(effective_from="2026-06-01", effective_stop="2026-01-01"))
    assert exc.value.field == "effective_stop"


def test_missing_recurrence_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        parse_income_form(_valid_form(recurrence=""))
    assert exc.value.field == "recurrence"


def test_unknown_recurrence_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        parse_income_form(_valid_form(recurrence="FORTNIGHTLY"))
    assert exc.value.field == "recurrence"


@pytest.mark.parametrize("bad", ["", "abc", "-5"])
def test_bad_quantity_rejected(bad: str) -> None:
    with pytest.raises(ValidationError) as exc:
        parse_income_form(_valid_form(quantity=bad))
    assert exc.value.field == "quantity"
