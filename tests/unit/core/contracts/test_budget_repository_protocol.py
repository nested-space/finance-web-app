"""Contract test: implementations satisfy the runtime-checkable Protocol."""

from __future__ import annotations

import pytest
from sqlmodel import Session

from finance_web_app.core.contracts.budget_repository import BudgetRepository
from finance_web_app.infrastructure.persistence.budget_repository import SqlBudgetRepository

pytestmark = pytest.mark.unit


def test_sql_repository_satisfies_protocol(session: Session) -> None:
    assert isinstance(SqlBudgetRepository(session), BudgetRepository)


def test_fake_repository_satisfies_protocol(fake_budget_repository: object) -> None:
    assert isinstance(fake_budget_repository, BudgetRepository)
