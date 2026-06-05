"""Unit tests for commitment form parsing/validation."""

from __future__ import annotations

from datetime import date

import pytest

from finance_web_app.core.contracts.errors import ValidationError
from finance_web_app.domain.recurrence import Recurrence
from finance_web_app.web.forms.commitment_form import parse_commitment_form

pytestmark = pytest.mark.unit


def _valid_form(**overrides: str) -> dict[str, str]:
    form = {
        "name": "Netflix",
        "quantity": "9.99",
        "category": "4",
        "recurrence": "MONTHLY",
        "effective_from": "2026-01-15",
        "length": "6",
        "length_unit": "MONTHS",
    }
    form.update(overrides)
    return form


def test_valid_form_coerces() -> None:
    parsed = parse_commitment_form(_valid_form())
    assert parsed.name == "Netflix"
    assert parsed.quantity.pence() == 999
    assert parsed.category_id == 4
    assert parsed.recurrence is Recurrence.MONTHLY
    assert parsed.effective_from == date(2026, 1, 15)
    assert parsed.effective_stop == date(2026, 7, 15)


@pytest.mark.parametrize(
    ("unit", "length", "expected"),
    [
        ("DAYS", "10", date(2026, 1, 25)),
        ("WEEKS", "2", date(2026, 1, 29)),
        ("MONTHS", "1", date(2026, 2, 15)),
        ("YEARS", "1", date(2027, 1, 15)),
    ],
)
def test_length_units_compute_stop(unit: str, length: str, expected: date) -> None:
    parsed = parse_commitment_form(_valid_form(length_unit=unit, length=length))
    assert parsed.effective_stop == expected


def test_months_length_clamps_to_month_end() -> None:
    parsed = parse_commitment_form(
        _valid_form(effective_from="2026-01-31", length="1", length_unit="MONTHS")
    )
    assert parsed.effective_stop == date(2026, 2, 28)


def test_once_only_needs_no_length_and_collapses_to_a_day() -> None:
    parsed = parse_commitment_form(
        {
            "name": "Setup",
            "quantity": "50",
            "category": "6",
            "recurrence": "ONCE_ONLY",
            "effective_from": "2026-03-15",
        }
    )
    assert parsed.recurrence is Recurrence.ONCE_ONLY
    assert parsed.effective_from == parsed.effective_stop == date(2026, 3, 15)


def test_length_required_for_recurring() -> None:
    with pytest.raises(ValidationError) as exc:
        parse_commitment_form(_valid_form(length=""))
    assert exc.value.field == "length"


@pytest.mark.parametrize("bad", ["", "ENTERTAINMENT", "0"])
def test_invalid_category_is_rejected(bad: str) -> None:
    with pytest.raises(ValidationError) as exc:
        parse_commitment_form(_valid_form(category=bad))
    assert exc.value.field == "category"


def test_recurrence_outside_subset_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        parse_commitment_form(_valid_form(recurrence="QUARTERLY"))
    assert exc.value.field == "recurrence"


@pytest.mark.parametrize("bad", ["", "abc", "-5"])
def test_bad_quantity_rejected(bad: str) -> None:
    with pytest.raises(ValidationError) as exc:
        parse_commitment_form(_valid_form(quantity=bad))
    assert exc.value.field == "quantity"
