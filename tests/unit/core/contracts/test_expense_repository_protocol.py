"""Contract test: expense implementations satisfy the Protocol."""

from __future__ import annotations

import pytest
from sqlmodel import Session

from finance_web_app.core.contracts.expense_repository import ExpenseRepository
from finance_web_app.infrastructure.persistence.expense_repository import SqlExpenseRepository

pytestmark = pytest.mark.unit


def test_sql_repository_satisfies_protocol(session: Session) -> None:
    assert isinstance(SqlExpenseRepository(session), ExpenseRepository)


def test_fake_repository_satisfies_protocol(fake_expense_repository: object) -> None:
    assert isinstance(fake_expense_repository, ExpenseRepository)
