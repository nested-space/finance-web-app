"""Domain records and the fixed category set.

Records are frozen dataclasses with an ``id`` that is ``None`` before
persistence. ``Category`` member *names* are the stable codes stored in the
database and constrained by ``schema.sql``; human display text is not here -- it
lives in ``web/rendering`` and is never persisted (``docs/ARCHITECTURE.md``).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from finance_web_app.domain.effective_period import EffectivePeriod
from finance_web_app.domain.money import Money


class Category(Enum):
    """Expense/budget categories. The member name is the persisted code."""

    OCCASIONAL = "OCCASIONAL"
    GROCERIES = "GROCERIES"
    CLOTHING = "CLOTHING"
    ENTERTAINMENT = "ENTERTAINMENT"
    PETROL = "PETROL"
    KIDS = "KIDS"
    CHRISTMAS = "CHRISTMAS"

    @classmethod
    def from_code(cls, code: str) -> Category:
        """Resolve a stored code to a ``Category``, raising ``ValueError`` if unknown."""
        try:
            return cls[code]
        except KeyError as exc:
            raise ValueError(f"unknown category: {code!r}") from exc


@dataclass(frozen=True)
class BudgetRecord:
    """A monthly spending cap for a category, effective over a date range."""

    name: str
    quantity: Money
    category: Category
    period: EffectivePeriod
    id: int | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name must be non-empty")
