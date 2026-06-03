"""Unit tests for calendar arithmetic with day-clamping."""

from __future__ import annotations

from datetime import date

import pytest

from finance_web_app.domain.calendar_math import add_months, add_years, clamp_day

pytestmark = pytest.mark.unit


def test_add_months_basic() -> None:
    assert add_months(date(2026, 1, 15), 1) == date(2026, 2, 15)


def test_add_months_clamps_to_month_end() -> None:
    # 2026 is not a leap year -> Feb has 28 days.
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)


def test_add_months_rolls_over_year() -> None:
    assert add_months(date(2026, 11, 15), 3) == date(2027, 2, 15)


def test_add_months_negative() -> None:
    assert add_months(date(2026, 1, 15), -1) == date(2025, 12, 15)


def test_add_years_basic() -> None:
    assert add_years(date(2026, 6, 1), 2) == date(2028, 6, 1)


def test_add_years_clamps_leap_day() -> None:
    assert add_years(date(2024, 2, 29), 1) == date(2025, 2, 28)


def test_clamp_day() -> None:
    assert clamp_day(31, 2026, 2) == 28
    assert clamp_day(15, 2026, 2) == 15
