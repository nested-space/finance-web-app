"""Unit tests for Recurrence.fires_on and code resolution."""

from __future__ import annotations

from datetime import date

import pytest

from finance_web_app.domain.recurrence import Recurrence

pytestmark = pytest.mark.unit


def test_nothing_fires_before_effective_from() -> None:
    start = date(2026, 6, 10)
    for rec in Recurrence:
        assert rec.fires_on(date(2026, 6, 9), start) is False


def test_daily_fires_every_day_on_or_after_start() -> None:
    start = date(2026, 6, 10)
    assert Recurrence.DAILY.fires_on(start, start) is True
    assert Recurrence.DAILY.fires_on(date(2026, 6, 11), start) is True


def test_once_only_fires_only_on_start() -> None:
    start = date(2026, 6, 10)
    assert Recurrence.ONCE_ONLY.fires_on(start, start) is True
    assert Recurrence.ONCE_ONLY.fires_on(date(2026, 6, 11), start) is False


def test_weekly_fires_on_same_weekday() -> None:
    start = date(2026, 6, 1)  # a Monday
    assert Recurrence.WEEKLY.fires_on(date(2026, 6, 8), start) is True  # next Monday
    assert Recurrence.WEEKLY.fires_on(date(2026, 6, 9), start) is False  # Tuesday


def test_monthly_fires_on_day_of_month() -> None:
    start = date(2026, 1, 15)
    assert Recurrence.MONTHLY.fires_on(date(2026, 3, 15), start) is True
    assert Recurrence.MONTHLY.fires_on(date(2026, 3, 16), start) is False


def test_monthly_clamps_to_short_month_end() -> None:
    start = date(2026, 1, 31)  # day 31
    assert Recurrence.MONTHLY.fires_on(date(2026, 2, 28), start) is True  # clamped
    assert Recurrence.MONTHLY.fires_on(date(2026, 2, 27), start) is False


@pytest.mark.parametrize(
    ("when", "expected"),
    [
        (date(2026, 1, 15), True),  # start
        (date(2026, 4, 15), True),  # +3
        (date(2026, 7, 15), True),  # +6
        (date(2027, 1, 15), True),  # +12
        (date(2026, 2, 15), False),  # +1
        (date(2026, 4, 16), False),  # right month, wrong day
    ],
)
def test_quarterly_cadence(when: date, expected: bool) -> None:
    assert Recurrence.QUARTERLY.fires_on(when, date(2026, 1, 15)) is expected


def test_annual_fires_on_month_and_day() -> None:
    start = date(2026, 3, 20)
    assert Recurrence.ANNUAL.fires_on(date(2027, 3, 20), start) is True
    assert Recurrence.ANNUAL.fires_on(date(2027, 3, 21), start) is False
    assert Recurrence.ANNUAL.fires_on(date(2027, 4, 20), start) is False


def test_annual_leap_day_anchor_clamps_in_non_leap_year() -> None:
    start = date(2024, 2, 29)  # leap day
    assert Recurrence.ANNUAL.fires_on(date(2025, 2, 28), start) is True  # clamped
    assert Recurrence.ANNUAL.fires_on(date(2028, 2, 29), start) is True  # leap year


def test_from_code() -> None:
    assert Recurrence.from_code("QUARTERLY") is Recurrence.QUARTERLY
    with pytest.raises(ValueError):
        Recurrence.from_code("FORTNIGHTLY")
