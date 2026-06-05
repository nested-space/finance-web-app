"""Canonical SQLModel records and the user-managed category table.

These ``table=True`` models are the schema source of truth; Alembic migrations
are generated from them. Value objects are preserved: ``quantity`` is stored via
the ``MoneyPence`` type and exposed as ``Money``, and ``effective_from`` /
``effective_stop`` are exposed together as an ``EffectivePeriod`` through the
``period`` property -- so the single ``covers_month`` predicate is unchanged.

``Category`` is a user-managed table (one shared list across budgets, budget
items, expenses, and commitments). Records reference it by ``category_id``; the
category *name* lives in the row, so there is no enum and no per-resource CHECK
of allowed codes -- the foreign key enforces validity instead. Spending
classification is two-level: ``Category`` carries the budget amount (via
``Budget``), ``BudgetItem`` is a named label under a category that carries no
amount, and an ``Expense`` is tagged with a category and an optional budget item.

CHECK constraints mirror the integrity the previous hand-written ``schema.sql``
enforced; the recurrence CHECKs stay (recurrence is still an enum).
"""

# NB: no ``from __future__ import annotations`` here -- SQLModel resolves
# ``Relationship`` targets from real (non-stringified) annotations, so this file
# evaluates annotations eagerly and uses explicit string forward refs instead.

import datetime as dt
from datetime import UTC, date, datetime

from sqlalchemy import CheckConstraint, Column, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from finance_web_app.domain.effective_period import EffectivePeriod
from finance_web_app.domain.money import Money, MoneyPence
from finance_web_app.domain.recurrence import Recurrence

# Recurrence stays an enum, so its CHECK sets are still declared from the single
# source. Commitments use a subset (no QUARTERLY); income may use every pattern.
COMMITMENT_RECURRENCES: tuple[Recurrence, ...] = (
    Recurrence.DAILY,
    Recurrence.WEEKLY,
    Recurrence.MONTHLY,
    Recurrence.ANNUAL,
    Recurrence.ONCE_ONLY,
)
_COMMITMENT_RECURRENCE_CODES = ", ".join(f"'{r.name}'" for r in COMMITMENT_RECURRENCES)
_INCOME_RECURRENCE_CODES = ", ".join(f"'{r.name}'" for r in Recurrence)


class Category(SQLModel, table=True):
    """A user-managed spending category, shared by every resource that classifies."""

    __tablename__ = "category"
    __table_args__ = (CheckConstraint("length(name) > 0", name="category_name_nonempty"),)

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Budget(SQLModel, table=True):
    """A monthly spending cap for a category, effective over a date range."""

    __tablename__ = "budget"
    model_config = {"arbitrary_types_allowed": True}
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="budget_quantity_nonneg"),
        CheckConstraint(
            "effective_stop IS NULL OR effective_stop >= effective_from",
            name="budget_effective_range",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    quantity: Money = Field(sa_column=Column(MoneyPence, nullable=False))
    category_id: int = Field(foreign_key="category.id")
    effective_from: date = Field(default_factory=date.today)
    effective_stop: date | None = Field(default=None)
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def period(self) -> EffectivePeriod:
        return EffectivePeriod(from_date=self.effective_from, stop_date=self.effective_stop)


class BudgetItem(SQLModel, table=True):
    """A named classification under a category; carries no budget amount of its own."""

    __tablename__ = "budget_item"
    __table_args__ = (CheckConstraint("length(name) > 0", name="budget_item_name_nonempty"),)

    id: int | None = Field(default=None, primary_key=True)
    name: str
    category_id: int = Field(foreign_key="category.id")
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Expense(SQLModel, table=True):
    """A one-off spend with an explicit date, a category, and an optional budget item."""

    __tablename__ = "expense"
    model_config = {"arbitrary_types_allowed": True}
    __table_args__ = (
        CheckConstraint("length(name) > 0", name="expense_name_nonempty"),
        CheckConstraint("quantity >= 0", name="expense_quantity_nonneg"),
    )

    id: int | None = Field(default=None, primary_key=True)
    name: str
    quantity: Money = Field(sa_column=Column(MoneyPence, nullable=False))
    category_id: int = Field(foreign_key="category.id")
    budget_item_id: int | None = Field(
        default=None, foreign_key="budget_item.id", ondelete="SET NULL"
    )
    # Annotated as ``dt.date`` (not bare ``date``) because a field named ``date``
    # would shadow the type name and break Pydantic's annotation resolution.
    date: dt.date = Field(default_factory=dt.date.today)
    description: str | None = Field(default=None)
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def in_month(self, year: int, month: int) -> bool:
        """Stricter date predicate for expenses (its own helper, not covers_month)."""
        return self.date.year == year and self.date.month == month


class Commitment(SQLModel, table=True):
    """A recurring outgoing (e.g. a subscription), effective over a date range."""

    __tablename__ = "commitment"
    model_config = {"arbitrary_types_allowed": True}
    __table_args__ = (
        CheckConstraint("length(name) > 0", name="commitment_name_nonempty"),
        CheckConstraint("quantity >= 0", name="commitment_quantity_nonneg"),
        CheckConstraint(
            f"recurrence IN ({_COMMITMENT_RECURRENCE_CODES})", name="commitment_recurrence_valid"
        ),
        CheckConstraint("effective_stop >= effective_from", name="commitment_effective_range"),
    )

    id: int | None = Field(default=None, primary_key=True)
    name: str
    quantity: Money = Field(sa_column=Column(MoneyPence, nullable=False))
    category_id: int = Field(foreign_key="category.id")
    recurrence: Recurrence
    effective_from: date = Field(default_factory=date.today)
    effective_stop: date
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def period(self) -> EffectivePeriod:
        return EffectivePeriod(from_date=self.effective_from, stop_date=self.effective_stop)


class Income(SQLModel, table=True):
    """A recurring income stream, with optional one-off exceptions."""

    __tablename__ = "income"
    model_config = {"arbitrary_types_allowed": True}
    __table_args__ = (
        CheckConstraint("length(name) > 0", name="income_name_nonempty"),
        CheckConstraint("quantity >= 0", name="income_quantity_nonneg"),
        CheckConstraint(
            f"recurrence IN ({_INCOME_RECURRENCE_CODES})", name="income_recurrence_valid"
        ),
        CheckConstraint(
            "effective_stop IS NULL OR effective_stop >= effective_from",
            name="income_effective_range",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    name: str
    quantity: Money = Field(sa_column=Column(MoneyPence, nullable=False))
    recurrence: Recurrence
    effective_from: date = Field(default_factory=date.today)
    effective_stop: date | None = Field(default=None)
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))
    exceptions: list["IncomeException"] = Relationship(
        back_populates="income",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    @property
    def period(self) -> EffectivePeriod:
        return EffectivePeriod(from_date=self.effective_from, stop_date=self.effective_stop)


class IncomeException(SQLModel, table=True):
    """A one-off override of a recurring income on a specific date.

    The exception's amount *replaces* the recurring amount for that day (applied
    by the finance model in C3). Deleting an income cascades to its exceptions.
    """

    __tablename__ = "income_exception"
    model_config = {"arbitrary_types_allowed": True}
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="income_exception_quantity_nonneg"),
        UniqueConstraint("income_id", "date", name="income_exception_unique_date"),
    )

    id: int | None = Field(default=None, primary_key=True)
    income_id: int = Field(foreign_key="income.id", ondelete="CASCADE")
    date: dt.date
    quantity: Money = Field(sa_column=Column(MoneyPence, nullable=False))
    reason: str | None = Field(default=None)
    income: Income | None = Relationship(back_populates="exceptions")


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
