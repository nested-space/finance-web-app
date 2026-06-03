"""Unit tests for EffectivePeriod.covers_month -- the single date-effective predicate."""

from __future__ import annotations

from datetime import date

import pytest

from finance_web_app.domain.effective_period import EffectivePeriod

pytestmark = pytest.mark.unit


def test_start_mid_month_is_inclusive() -> None:
    period = EffectivePeriod(from_date=date(2026, 6, 15))
    assert period.covers_month(2026, 6) is True


def test_open_ended_covers_all_later_months() -> None:
    period = EffectivePeriod(from_date=date(2026, 1, 1))
    assert period.covers_month(2030, 12) is True


def test_stop_on_first_of_month_still_covers() -> None:
    period = EffectivePeriod(from_date=date(2026, 1, 1), stop_date=date(2026, 6, 1))
    assert period.covers_month(2026, 6) is True


def test_month_before_start_is_not_covered() -> None:
    period = EffectivePeriod(from_date=date(2026, 6, 1))
    assert period.covers_month(2026, 5) is False


def test_month_after_stop_is_not_covered() -> None:
    period = EffectivePeriod(from_date=date(2026, 1, 1), stop_date=date(2026, 5, 31))
    assert period.covers_month(2026, 6) is False


def test_start_on_last_day_of_month_is_covered() -> None:
    period = EffectivePeriod(from_date=date(2026, 6, 30))
    assert period.covers_month(2026, 6) is True


@pytest.mark.parametrize("month", [1, 12])
def test_months_are_one_indexed(month: int) -> None:
    period = EffectivePeriod(from_date=date(2026, month, 1))
    assert period.covers_month(2026, month) is True


@pytest.mark.parametrize("month", [0, 13, -1])
def test_out_of_range_month_raises(month: int) -> None:
    with pytest.raises(ValueError):
        EffectivePeriod(from_date=date(2026, 1, 1)).covers_month(2026, month)


def test_stop_before_start_violates_invariant() -> None:
    with pytest.raises(ValueError):
        EffectivePeriod(from_date=date(2026, 6, 10), stop_date=date(2026, 6, 1))
