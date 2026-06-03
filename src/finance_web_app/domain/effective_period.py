"""EffectivePeriod value object.

Holds the date range over which a record is effective and owns the *single*
date-effective predicate, ``covers_month``. This predicate is defined here and
nowhere else; services call it rather than re-implementing date maths. See
``docs/ARCHITECTURE.md`` -> "Bug-fix decisions".
"""

from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class EffectivePeriod:
    """A ``[from_date, stop_date]`` range; ``stop_date`` of ``None`` is open-ended."""

    from_date: date
    stop_date: date | None = None

    def __post_init__(self) -> None:
        if self.stop_date is not None and self.stop_date < self.from_date:
            raise ValueError("stop_date must be on or after from_date")

    def covers_month(self, year: int, month: int) -> bool:
        """Whether this period is effective during ``(year, month)`` (1-indexed month).

        A period covers the month if it starts on or before the last day of the
        month and has not already stopped before the first day. "Starts this
        month" is inclusive.
        """
        if not 1 <= month <= 12:
            raise ValueError("month must be in 1..12")
        first_of_month = date(year, month, 1)
        last_of_month = date(year, month, monthrange(year, month)[1])
        return self.from_date <= last_of_month and (
            self.stop_date is None or self.stop_date >= first_of_month
        )
