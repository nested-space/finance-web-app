"""Unit tests for CategoryService against a fake repository."""

from __future__ import annotations

import pytest

from finance_web_app.application.services.category_service import CategoryService
from finance_web_app.core.contracts.category_repository import CategoryRepository
from finance_web_app.core.contracts.errors import NotFoundError, ValidationError

pytestmark = pytest.mark.unit


def test_create_adds_a_category(category_service: CategoryService) -> None:
    created = category_service.create(name="Holidays")
    assert created.id is not None
    assert any(c.name == "Holidays" for c in category_service.list_all())


def test_create_blank_name_raises(category_service: CategoryService) -> None:
    with pytest.raises(ValidationError) as exc:
        category_service.create(name="   ")
    assert exc.value.field == "name"


def test_create_duplicate_name_raises_case_insensitively(
    category_service: CategoryService,
) -> None:
    with pytest.raises(ValidationError):
        category_service.create(name="groceries")  # "Groceries" is seeded


def test_delete_removes_an_unused_category(category_service: CategoryService) -> None:
    created = category_service.create(name="Holidays")
    assert created.id is not None
    category_service.delete(created.id)
    assert all(c.name != "Holidays" for c in category_service.list_all())


def test_delete_blocked_while_in_use(
    category_service: CategoryService,
    fake_category_repository: CategoryRepository,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(fake_category_repository, "count_references", lambda _category_id: 3)
    with pytest.raises(ValidationError) as exc:
        category_service.delete(2)  # Groceries
    assert exc.value.field == "category"


def test_delete_missing_raises_not_found(category_service: CategoryService) -> None:
    with pytest.raises(NotFoundError):
        category_service.delete(999)
