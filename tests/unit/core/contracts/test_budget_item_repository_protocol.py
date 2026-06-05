"""Contract test: implementations satisfy the runtime-checkable Protocol."""

from __future__ import annotations

import pytest
from sqlmodel import Session

from finance_web_app.core.contracts.budget_item_repository import BudgetItemRepository
from finance_web_app.infrastructure.persistence.budget_item_repository import (
    SqlBudgetItemRepository,
)

pytestmark = pytest.mark.unit


def test_sql_repository_satisfies_protocol(session: Session) -> None:
    assert isinstance(SqlBudgetItemRepository(session), BudgetItemRepository)


def test_fake_repository_satisfies_protocol(fake_budget_item_repository: object) -> None:
    assert isinstance(fake_budget_item_repository, BudgetItemRepository)
