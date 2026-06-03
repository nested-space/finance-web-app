"""Contract test: income implementations satisfy the Protocol."""

from __future__ import annotations

import pytest
from sqlmodel import Session

from finance_web_app.core.contracts.income_repository import IncomeRepository
from finance_web_app.infrastructure.persistence.income_repository import SqlIncomeRepository

pytestmark = pytest.mark.unit


def test_sql_repository_satisfies_protocol(session: Session) -> None:
    assert isinstance(SqlIncomeRepository(session), IncomeRepository)


def test_fake_repository_satisfies_protocol(fake_income_repository: object) -> None:
    assert isinstance(fake_income_repository, IncomeRepository)
