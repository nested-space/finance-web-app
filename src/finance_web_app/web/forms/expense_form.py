"""Expense form parsing and validation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

from finance_web_app.core.contracts.errors import ValidationError
from finance_web_app.domain.money import Money


@dataclass(frozen=True)
class ParsedExpense:
    name: str
    quantity: Money
    category_id: int
    budget_item_id: int | None
    date: date
    description: str | None


def parse_expense_form(form: Mapping[str, str]) -> ParsedExpense:
    name = form.get("name", "").strip()
    if not name:
        raise ValidationError("name", "is required")

    try:
        quantity = Money.from_form_string(form.get("quantity", ""))
    except ValueError as exc:
        raise ValidationError("quantity", str(exc)) from exc

    category_id = _parse_category_id(form.get("category", ""))
    budget_item_id = _parse_optional_budget_item_id(form.get("budget_item", ""))
    incurred = _parse_required_date(form.get("date", ""), "date")
    description = form.get("description", "").strip() or None

    return ParsedExpense(
        name=name,
        quantity=quantity,
        category_id=category_id,
        budget_item_id=budget_item_id,
        date=incurred,
        description=description,
    )


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


def _parse_optional_budget_item_id(raw: str) -> int | None:
    text = raw.strip()
    if not text:
        return None
    try:
        value = int(text)
    except ValueError as exc:
        raise ValidationError("budget_item", "must be a budget item") from exc
    if value < 1:
        raise ValidationError("budget_item", "must be a budget item")
    return value


def _parse_required_date(raw: str, field: str) -> date:
    text = raw.strip()
    if not text:
        raise ValidationError(field, "is required")
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValidationError(field, "must be a valid date (YYYY-MM-DD)") from exc
