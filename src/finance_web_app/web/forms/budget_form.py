"""Budget form parsing and validation.

Coerces raw request-body strings into domain value objects, translating any
rejection into a typed ``ValidationError``. Depends only on ``domain`` and the
contract errors (``docs/ARCHITECTURE.md`` -> "Layer map").
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

from finance_web_app.core.contracts.errors import ValidationError
from finance_web_app.domain.effective_period import EffectivePeriod
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import Category


@dataclass(frozen=True)
class ParsedBudget:
    """Validated budget fields, ready for the service to assemble into a record."""

    name: str
    quantity: Money
    category: Category
    period: EffectivePeriod


def parse_budget_form(form: Mapping[str, str]) -> ParsedBudget:
    name = form.get("name", "").strip()
    if not name:
        raise ValidationError("name", "is required")

    try:
        quantity = Money.from_form_string(form.get("quantity", ""))
    except ValueError as exc:
        raise ValidationError("quantity", str(exc)) from exc

    category = _parse_category(form.get("category", ""))
    effective_from = _parse_optional_date(form.get("effective_from", ""), "effective_from")
    effective_stop = _parse_optional_date(form.get("effective_stop", ""), "effective_stop")

    try:
        period = EffectivePeriod(from_date=effective_from or date.today(), stop_date=effective_stop)
    except ValueError as exc:
        raise ValidationError("effective_stop", str(exc)) from exc

    return ParsedBudget(name=name, quantity=quantity, category=category, period=period)


def _parse_category(raw: str) -> Category:
    code = raw.strip()
    if not code:
        raise ValidationError("category", "is required")
    try:
        return Category.from_code(code)
    except ValueError as exc:
        raise ValidationError("category", str(exc)) from exc


def _parse_optional_date(raw: str, field: str) -> date | None:
    text = raw.strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValidationError(field, "must be a valid date (YYYY-MM-DD)") from exc
