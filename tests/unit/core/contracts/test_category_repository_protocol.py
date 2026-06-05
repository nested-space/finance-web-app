"""Contract test: implementations satisfy the runtime-checkable Protocol."""

from __future__ import annotations

import pytest
from sqlmodel import Session

from finance_web_app.core.contracts.category_repository import CategoryRepository
from finance_web_app.infrastructure.persistence.category_repository import SqlCategoryRepository

pytestmark = pytest.mark.unit


def test_sql_repository_satisfies_protocol(session: Session) -> None:
    assert isinstance(SqlCategoryRepository(session), CategoryRepository)


def test_fake_repository_satisfies_protocol(fake_category_repository: object) -> None:
    assert isinstance(fake_category_repository, CategoryRepository)
