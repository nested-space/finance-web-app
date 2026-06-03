"""Unit tests for the Money value object."""

from __future__ import annotations

from decimal import Decimal

import pytest

from finance_web_app.domain.money import Money

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("pence", [0, 1, 99, 1299, 1000000])
def test_pence_round_trip_is_exact(pence: int) -> None:
    assert Money.from_pence(pence).pence() == pence


def test_from_form_string_parses_two_decimals() -> None:
    assert Money.from_form_string("12.99").pence() == 1299


def test_from_form_string_normalises_single_decimal() -> None:
    assert str(Money.from_form_string("1.5")) == "1.50"


def test_str_always_two_decimals() -> None:
    assert str(Money.from_pence(500)) == "5.00"


@pytest.mark.parametrize("raw", ["-1", "-0.01", "abc", "", "   ", "1.2.3", "NaN", "Infinity"])
def test_from_form_string_rejects_bad_input(raw: str) -> None:
    with pytest.raises(ValueError):
        Money.from_form_string(raw)


def test_sub_penny_precision_is_rejected() -> None:
    with pytest.raises(ValueError):
        Money(Decimal("1.234"))


def test_negative_construction_is_rejected() -> None:
    with pytest.raises(ValueError):
        Money(Decimal("-5.00"))


def test_from_pence_rejects_negative() -> None:
    with pytest.raises(ValueError):
        Money.from_pence(-1)


def test_split_evenly_is_exact_and_distributes_remainder() -> None:
    parts = Money.from_pence(1000).split_evenly(3)  # £10.00 / 3
    assert [p.pence() for p in parts] == [334, 333, 333]
    assert sum(p.pence() for p in parts) == 1000


def test_split_evenly_divisible() -> None:
    parts = Money.from_pence(900).split_evenly(3)
    assert [p.pence() for p in parts] == [300, 300, 300]


def test_split_evenly_rejects_zero_parts() -> None:
    with pytest.raises(ValueError):
        Money.from_pence(100).split_evenly(0)
