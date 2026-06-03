"""Recurrence value object and the firing predicate.

A recurring record fires relative to its own ``effective_from`` — there are no
stored ``day_of_*`` fields. ``fires_on`` is the single home for the firing rules
(``docs/ARCHITECTURE.md`` -> "FinanceModelService contract"); services call it
rather than matching on the enum.
"""

from __future__ import annotations

from datetime import date
from enum import Enum

from finance_web_app.domain.calendar_math import clamp_day


class Recurrence(Enum):
    """Recurrence patterns. The member name is the persisted code.

    Income may use all six; commitments use all except ``QUARTERLY``.
    """

    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    ANNUAL = "ANNUAL"
    ONCE_ONLY = "ONCE_ONLY"

    @classmethod
    def from_code(cls, code: str) -> Recurrence:
        """Resolve a stored code to a ``Recurrence``, raising ``ValueError`` if unknown."""
        try:
            return cls[code]
        except KeyError as exc:
            raise ValueError(f"unknown recurrence: {code!r}") from exc

    def fires_on(self, when: date, effective_from: date) -> bool:
        """Whether a record starting on ``effective_from`` fires on ``when``.

        Nothing fires before it starts. ``DAILY`` every day; ``WEEKLY`` on the
        weekday of ``effective_from``; ``MONTHLY`` on its day-of-month (clamped to
        month end); ``QUARTERLY`` likewise every third month; ``ANNUAL`` on its
        month+day (a Feb-29 anchor clamps to Feb 28 in non-leap years);
        ``ONCE_ONLY`` exactly on ``effective_from``.
        """
        if when < effective_from:
            return False
        if self is Recurrence.DAILY:
            return True
        if self is Recurrence.ONCE_ONLY:
            return when == effective_from
        if self is Recurrence.WEEKLY:
            return when.weekday() == effective_from.weekday()

        anchor_day = clamp_day(effective_from.day, when.year, when.month)
        if self is Recurrence.MONTHLY:
            return when.day == anchor_day
        if self is Recurrence.QUARTERLY:
            months = (when.year - effective_from.year) * 12 + (when.month - effective_from.month)
            return months % 3 == 0 and when.day == anchor_day
        if self is Recurrence.ANNUAL:
            return when.month == effective_from.month and when.day == anchor_day

        raise AssertionError(f"unhandled recurrence: {self!r}")
