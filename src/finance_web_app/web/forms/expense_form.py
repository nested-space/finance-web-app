"""Expense form parsing and validation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

from finance_web_app.core.contracts.errors import ValidationError
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import Category


@dataclass(frozen=True)
class ParsedExpense:
    name: str
    quantity: Money
    category: Category
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

    category = _parse_category(form.get("category", ""))
    incurred = _parse_required_date(form.get("date", ""), "date")
    description = form.get("description", "").strip() or None

    return ParsedExpense(
        name=name,
        quantity=quantity,
        category=category,
        date=incurred,
        description=description,
    )


def _parse_category(raw: str) -> Category:
    code = raw.strip()
    if not code:
        raise ValidationError("category", "is required")
    try:
        return Category.from_code(code)
    except ValueError as exc:
        raise ValidationError("category", str(exc)) from exc


def _parse_required_date(raw: str, field: str) -> date:
    text = raw.strip()
    if not text:
        raise ValidationError(field, "is required")
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValidationError(field, "must be a valid date (YYYY-MM-DD)") from exc
