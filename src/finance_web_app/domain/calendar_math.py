"""Calendar arithmetic with day-clamping (stdlib only).

Adding months or years can land on a day the target month lacks (e.g. Jan 31 +
1 month). We clamp to the last valid day of the target month — the same rule the
recurrence predicate uses for month-anchored firing.
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date


def clamp_day(day: int, year: int, month: int) -> int:
    """The given day-of-month, clamped to the last valid day of (year, month)."""
    return min(day, monthrange(year, month)[1])


def add_months(d: date, months: int) -> date:
    total = d.month - 1 + months
    year = d.year + total // 12
    month = total % 12 + 1
    return date(year, month, clamp_day(d.day, year, month))


def add_years(d: date, years: int) -> date:
    return add_months(d, years * 12)
