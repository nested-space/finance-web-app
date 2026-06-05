"""Budget item form parsing and validation.

A budget item is a named label under a category; that the ``category`` id exists
is checked by the service.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from finance_web_app.core.contracts.errors import ValidationError


@dataclass(frozen=True)
class ParsedBudgetItem:
    name: str
    category_id: int


def parse_budget_item_form(form: Mapping[str, str]) -> ParsedBudgetItem:
    name = form.get("name", "").strip()
    if not name:
        raise ValidationError("name", "is required")
    category_id = _parse_category_id(form.get("category", ""))
    return ParsedBudgetItem(name=name, category_id=category_id)


def _parse_category_id(raw: str) -> int:
    text = raw.strip()
    if not text:
        raise ValidationError("category", "is required")
    try:
        value = int(text)
    except ValueError as exc:
        raise ValidationError("category", "must be a category") from exc
    if value < 1:
        raise ValidationError("category", "must be a category")
    return value
