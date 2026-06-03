"""Canonical SQLModel records and the fixed category set.

These ``table=True`` models are the schema source of truth; Alembic migrations
are generated from them. Value objects are preserved: ``quantity`` is stored via
the ``MoneyPence`` type and exposed as ``Money``, and ``effective_from`` /
``effective_stop`` are exposed together as an ``EffectivePeriod`` through the
``period`` property -- so the single ``covers_month`` predicate is unchanged.

CHECK constraints mirror the integrity the previous hand-written ``schema.sql``
enforced; SQLAlchemy's ``Enum`` does not emit one by default
(``create_constraint`` is ``False``), so the category CHECK is declared here.
"""

from __future__ import annotations

import datetime as dt
from datetime import UTC, date, datetime
from enum import Enum

from sqlalchemy import CheckConstraint, Column
from sqlmodel import Field, SQLModel

from finance_web_app.domain.effective_period import EffectivePeriod
from finance_web_app.domain.money import Money, MoneyPence

_CATEGORY_CODES = (
    "'OCCASIONAL', 'GROCERIES', 'CLOTHING', 'ENTERTAINMENT', 'PETROL', 'KIDS', 'CHRISTMAS'"
)


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


class Budget(SQLModel, table=True):
    """A monthly spending cap for a category, effective over a date range."""

    __tablename__ = "budget"
    model_config = {"arbitrary_types_allowed": True}
    __table_args__ = (
        CheckConstraint("length(name) > 0", name="budget_name_nonempty"),
        CheckConstraint("quantity >= 0", name="budget_quantity_nonneg"),
        CheckConstraint(f"category IN ({_CATEGORY_CODES})", name="budget_category_valid"),
        CheckConstraint(
            "effective_stop IS NULL OR effective_stop >= effective_from",
            name="budget_effective_range",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    name: str
    quantity: Money = Field(sa_column=Column(MoneyPence, nullable=False))
    category: Category
    effective_from: date = Field(default_factory=date.today)
    effective_stop: date | None = Field(default=None)
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def period(self) -> EffectivePeriod:
        return EffectivePeriod(from_date=self.effective_from, stop_date=self.effective_stop)


class Expense(SQLModel, table=True):
    """A one-off spend with an explicit date and a fixed-set category."""

    __tablename__ = "expense"
    model_config = {"arbitrary_types_allowed": True}
    __table_args__ = (
        CheckConstraint("length(name) > 0", name="expense_name_nonempty"),
        CheckConstraint("quantity >= 0", name="expense_quantity_nonneg"),
        CheckConstraint(f"category IN ({_CATEGORY_CODES})", name="expense_category_valid"),
    )

    id: int | None = Field(default=None, primary_key=True)
    name: str
    quantity: Money = Field(sa_column=Column(MoneyPence, nullable=False))
    category: Category
    # Annotated as ``dt.date`` (not bare ``date``) because a field named ``date``
    # would shadow the type name and break Pydantic's annotation resolution.
    date: dt.date = Field(default_factory=dt.date.today)
    description: str | None = Field(default=None)
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def in_month(self, year: int, month: int) -> bool:
        """Stricter date predicate for expenses (its own helper, not covers_month)."""
        return self.date.year == year and self.date.month == month


class User(SQLModel, table=True):
    """Scaffold-only account table; no route reads or writes it in v1.0.0."""

    __tablename__ = "user"
    __table_args__ = (
        CheckConstraint("length(username) > 0", name="user_username_nonempty"),
        CheckConstraint("length(password_hash) > 0", name="user_password_hash_nonempty"),
    )

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    password_hash: str
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))
