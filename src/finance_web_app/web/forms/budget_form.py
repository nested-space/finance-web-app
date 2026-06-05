"""Budget form parsing and validation.

Coerces raw request-body strings into domain value objects, translating any
rejection into a typed ``ValidationError``. ``category`` is the id of a
user-managed category; that the id *exists* is checked by the service. Depends
only on ``domain`` and the contract errors (``docs/ARCHITECTURE.md`` -> "Layer
map").
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

from finance_web_app.core.contracts.errors import ValidationError
from finance_web_app.domain.effective_period import EffectivePeriod
from finance_web_app.domain.money import Money


@dataclass(frozen=True)
class ParsedBudget:
    """Validated budget fields, ready for the service to assemble into a record."""

    quantity: Money
    category_id: int
    period: EffectivePeriod


def parse_budget_form(form: Mapping[str, str]) -> ParsedBudget:
    try:
        quantity = Money.from_form_string(form.get("quantity", ""))
    except ValueError as exc:
        raise ValidationError("quantity", str(exc)) from exc

    category_id = _parse_category_id(form.get("category", ""))
    effective_from = _parse_optional_date(form.get("effective_from", ""), "effective_from")
    effective_stop = _parse_optional_date(form.get("effective_stop", ""), "effective_stop")

    try:
        period = EffectivePeriod(from_date=effective_from or date.today(), stop_date=effective_stop)
    except ValueError as exc:
        raise ValidationError("effective_stop", str(exc)) from exc

    return ParsedBudget(quantity=quantity, category_id=category_id, period=period)


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


def _parse_optional_date(raw: str, field: str) -> date | None:
    text = raw.strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValidationError(field, "must be a valid date (YYYY-MM-DD)") from exc
