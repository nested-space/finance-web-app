"""Shared test fixtures.

An in-memory engine/session with the schema applied for repository tests, a Flask
test client (wired to a temp-file DB, migrated by the app factory) for web tests,
and dict-backed fake repositories for service tests so they never touch SQL
(``docs/DEVELOPMENT.md`` -> "Fixtures").

The fake category repository is seeded with the seven categories that were fixed
before they became user-managed, so service tests can reference them by id via the
``SEED_CATEGORY_IDS`` map (e.g. ``SEED_CATEGORY_IDS["Groceries"]``).
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest
from flask.testing import FlaskClient
from sqlalchemy import Engine
from sqlmodel import Session, SQLModel

from finance_web_app.application.services.budget_item_service import BudgetItemService
from finance_web_app.application.services.budget_service import BudgetService
from finance_web_app.application.services.category_service import CategoryService
from finance_web_app.application.services.commitment_service import CommitmentService
from finance_web_app.application.services.expense_service import ExpenseService
from finance_web_app.application.services.finance_model_service import FinanceModelService
from finance_web_app.application.services.history_service import HistoryService
from finance_web_app.application.services.income_service import IncomeService
from finance_web_app.application.services.insights_service import InsightsService
from finance_web_app.core.contracts.errors import NotFoundError
from finance_web_app.core.runtime.app_factory import create_app
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import (
    Budget,
    BudgetItem,
    Category,
    Commitment,
    Expense,
    Income,
    IncomeException,
)
from finance_web_app.infrastructure.persistence.engine import make_engine, make_session

# The seven previously-fixed categories, in their original order. Seeded into the
# fake category repository so ids 1..7 are stable across service tests.
_SEED_CATEGORY_NAMES = (
    "Occasional",
    "Groceries",
    "Clothing",
    "Entertainment",
    "Petrol",
    "Kids",
    "Christmas",
)
SEED_CATEGORY_IDS = {name: index for index, name in enumerate(_SEED_CATEGORY_NAMES, start=1)}


@pytest.fixture
def engine() -> Iterator[Engine]:
    eng = make_engine(":memory:")
    SQLModel.metadata.create_all(eng)
    try:
        yield eng
    finally:
        eng.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    with make_session(engine) as db_session:
        yield db_session


@pytest.fixture
def flask_client(tmp_path: Path) -> FlaskClient:
    app = create_app(db_path=str(tmp_path / "finance.db"))
    app.config.update(TESTING=True)
    return app.test_client()


class FakeCategoryRepository:
    """In-memory ``CategoryRepository`` for service tests, pre-seeded with seven categories."""

    def __init__(self, *, seed: bool = True) -> None:
        self._rows: dict[int, Category] = {}
        self._references: dict[int, int] = {}
        self._next_id = 1
        if seed:
            for name in _SEED_CATEGORY_NAMES:
                self.create(Category(name=name))

    def list_all(self) -> list[Category]:
        return sorted(self._rows.values(), key=lambda c: c.name)

    def get(self, category_id: int) -> Category:
        try:
            return self._rows[category_id]
        except KeyError:
            raise NotFoundError("category", category_id) from None

    def create(self, record: Category) -> Category:
        record.id = self._next_id
        self._rows[self._next_id] = record
        self._next_id += 1
        return record

    def delete(self, category_id: int) -> None:
        if category_id not in self._rows:
            raise NotFoundError("category", category_id)
        del self._rows[category_id]

    def count_references(self, category_id: int) -> int:
        return self._references.get(category_id, 0)

    def set_references(self, category_id: int, count: int) -> None:
        """Test hook: simulate a category being in use by other resources."""
        self._references[category_id] = count


@pytest.fixture
def fake_category_repository() -> FakeCategoryRepository:
    return FakeCategoryRepository()


@pytest.fixture
def category_service(fake_category_repository: FakeCategoryRepository) -> CategoryService:
    return CategoryService(fake_category_repository)


class FakeBudgetItemRepository:
    """In-memory ``BudgetItemRepository`` for service tests."""

    def __init__(self) -> None:
        self._rows: dict[int, BudgetItem] = {}
        self._next_id = 1

    def list_all(self) -> list[BudgetItem]:
        return [self._rows[key] for key in sorted(self._rows)]

    def list_by_category(self, category_id: int) -> list[BudgetItem]:
        return [item for item in self.list_all() if item.category_id == category_id]

    def get(self, budget_item_id: int) -> BudgetItem:
        try:
            return self._rows[budget_item_id]
        except KeyError:
            raise NotFoundError("budget_item", budget_item_id) from None

    def create(self, record: BudgetItem) -> BudgetItem:
        record.id = self._next_id
        self._rows[self._next_id] = record
        self._next_id += 1
        return record

    def delete(self, budget_item_id: int) -> None:
        if budget_item_id not in self._rows:
            raise NotFoundError("budget_item", budget_item_id)
        del self._rows[budget_item_id]


@pytest.fixture
def fake_budget_item_repository() -> FakeBudgetItemRepository:
    return FakeBudgetItemRepository()


@pytest.fixture
def budget_item_service(
    fake_budget_item_repository: FakeBudgetItemRepository,
    fake_category_repository: FakeCategoryRepository,
) -> BudgetItemService:
    return BudgetItemService(fake_budget_item_repository, fake_category_repository)


class FakeBudgetRepository:
    """In-memory ``BudgetRepository`` for service tests."""

    def __init__(self) -> None:
        self._rows: dict[int, Budget] = {}
        self._next_id = 1

    def list_all(self) -> list[Budget]:
        return [self._rows[key] for key in sorted(self._rows)]

    def list_effective(self, year: int, month: int) -> list[Budget]:
        return [b for b in self.list_all() if b.period.covers_month(year, month)]

    def get(self, budget_id: int) -> Budget:
        try:
            return self._rows[budget_id]
        except KeyError:
            raise NotFoundError("budget", budget_id) from None

    def create(self, record: Budget) -> Budget:
        record.id = self._next_id
        self._rows[self._next_id] = record
        self._next_id += 1
        return record

    def delete(self, budget_id: int) -> None:
        if budget_id not in self._rows:
            raise NotFoundError("budget", budget_id)
        del self._rows[budget_id]


@pytest.fixture
def fake_budget_repository() -> FakeBudgetRepository:
    return FakeBudgetRepository()


@pytest.fixture
def budget_service(
    fake_budget_repository: FakeBudgetRepository,
    fake_category_repository: FakeCategoryRepository,
) -> BudgetService:
    return BudgetService(fake_budget_repository, fake_category_repository)


class FakeExpenseRepository:
    """In-memory ``ExpenseRepository`` for service tests."""

    def __init__(self) -> None:
        self._rows: dict[int, Expense] = {}
        self._next_id = 1

    def list_all(self) -> list[Expense]:
        return [self._rows[key] for key in sorted(self._rows)]

    def list_effective(self, year: int, month: int) -> list[Expense]:
        return [e for e in self.list_all() if e.in_month(year, month)]

    def get(self, expense_id: int) -> Expense:
        try:
            return self._rows[expense_id]
        except KeyError:
            raise NotFoundError("expense", expense_id) from None

    def create(self, record: Expense) -> Expense:
        record.id = self._next_id
        self._rows[self._next_id] = record
        self._next_id += 1
        return record

    def delete(self, expense_id: int) -> None:
        if expense_id not in self._rows:
            raise NotFoundError("expense", expense_id)
        del self._rows[expense_id]


@pytest.fixture
def fake_expense_repository() -> FakeExpenseRepository:
    return FakeExpenseRepository()


@pytest.fixture
def expense_service(
    fake_expense_repository: FakeExpenseRepository,
    fake_category_repository: FakeCategoryRepository,
    fake_budget_item_repository: FakeBudgetItemRepository,
) -> ExpenseService:
    return ExpenseService(
        fake_expense_repository, fake_category_repository, fake_budget_item_repository
    )


@pytest.fixture
def history_service(
    budget_service: BudgetService, expense_service: ExpenseService
) -> HistoryService:
    return HistoryService(budget_service, expense_service)


class FakeCommitmentRepository:
    """In-memory ``CommitmentRepository`` for service tests."""

    def __init__(self) -> None:
        self._rows: dict[int, Commitment] = {}
        self._next_id = 1

    def list_all(self) -> list[Commitment]:
        return [self._rows[key] for key in sorted(self._rows)]

    def list_effective(self, year: int, month: int) -> list[Commitment]:
        return [c for c in self.list_all() if c.period.covers_month(year, month)]

    def get(self, commitment_id: int) -> Commitment:
        try:
            return self._rows[commitment_id]
        except KeyError:
            raise NotFoundError("commitment", commitment_id) from None

    def create(self, record: Commitment) -> Commitment:
        record.id = self._next_id
        self._rows[self._next_id] = record
        self._next_id += 1
        return record

    def delete(self, commitment_id: int) -> None:
        if commitment_id not in self._rows:
            raise NotFoundError("commitment", commitment_id)
        del self._rows[commitment_id]


@pytest.fixture
def fake_commitment_repository() -> FakeCommitmentRepository:
    return FakeCommitmentRepository()


@pytest.fixture
def commitment_service(
    fake_commitment_repository: FakeCommitmentRepository,
    fake_category_repository: FakeCategoryRepository,
) -> CommitmentService:
    return CommitmentService(fake_commitment_repository, fake_category_repository)


class FakeIncomeRepository:
    """In-memory ``IncomeRepository`` for service tests (with exceptions)."""

    def __init__(self) -> None:
        self._rows: dict[int, Income] = {}
        self._exceptions: list[IncomeException] = []
        self._next_id = 1

    def list_all(self) -> list[Income]:
        return [self._rows[key] for key in sorted(self._rows)]

    def list_effective(self, year: int, month: int) -> list[Income]:
        return [i for i in self.list_all() if i.period.covers_month(year, month)]

    def get(self, income_id: int) -> Income:
        try:
            return self._rows[income_id]
        except KeyError:
            raise NotFoundError("income", income_id) from None

    def create(self, record: Income) -> Income:
        record.id = self._next_id
        self._rows[self._next_id] = record
        self._next_id += 1
        return record

    def delete(self, income_id: int) -> None:
        if income_id not in self._rows:
            raise NotFoundError("income", income_id)
        del self._rows[income_id]
        self._exceptions = [e for e in self._exceptions if e.income_id != income_id]

    def add_exception(self, income_id: int, exception: IncomeException) -> None:
        exception.income_id = income_id
        self._exceptions.append(exception)

    def list_exceptions(self, income_id: int) -> list[IncomeException]:
        return [e for e in self._exceptions if e.income_id == income_id]


@pytest.fixture
def fake_income_repository() -> FakeIncomeRepository:
    return FakeIncomeRepository()


@pytest.fixture
def income_service(fake_income_repository: FakeIncomeRepository) -> IncomeService:
    return IncomeService(fake_income_repository)


@pytest.fixture
def finance_model_service(
    fake_income_repository: FakeIncomeRepository,
    fake_commitment_repository: FakeCommitmentRepository,
    fake_expense_repository: FakeExpenseRepository,
    fake_budget_repository: FakeBudgetRepository,
) -> FinanceModelService:
    return FinanceModelService(
        fake_income_repository,
        fake_commitment_repository,
        fake_expense_repository,
        fake_budget_repository,
    )


@pytest.fixture
def insights_service(
    finance_model_service: FinanceModelService,
    fake_expense_repository: FakeExpenseRepository,
    fake_budget_repository: FakeBudgetRepository,
    fake_category_repository: FakeCategoryRepository,
) -> InsightsService:
    return InsightsService(
        finance_model_service,
        fake_expense_repository,
        fake_budget_repository,
        fake_category_repository,
    )


@pytest.fixture
def seeded_repositories(
    fake_budget_repository: FakeBudgetRepository,
) -> dict[str, FakeBudgetRepository]:
    fake_budget_repository.create(
        Budget(
            quantity=Money.from_pence(20000),
            category_id=SEED_CATEGORY_IDS["Groceries"],
            effective_from=date(2026, 1, 1),
        )
    )
    return {"budgets": fake_budget_repository}
