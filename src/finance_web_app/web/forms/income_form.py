"""Income form parsing and validation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

from finance_web_app.core.contracts.errors import ValidationError
from finance_web_app.domain.money import Money
from finance_web_app.domain.recurrence import Recurrence


@dataclass(frozen=True)
class ParsedIncome:
    name: str
    quantity: Money
    recurrence: Recurrence
    effective_from: date
    effective_stop: date | None


def parse_income_form(form: Mapping[str, str]) -> ParsedIncome:
    name = form.get("name", "").strip()
    if not name:
        raise ValidationError("name", "is required")

    try:
        quantity = Money.from_form_string(form.get("quantity", ""))
    except ValueError as exc:
        raise ValidationError("quantity", str(exc)) from exc

    recurrence = _parse_recurrence(form.get("recurrence", ""))
    effective_from = _parse_required_date(form.get("effective_from", ""), "effective_from")
    effective_stop = _parse_optional_date(form.get("effective_stop", ""), "effective_stop")

    if effective_stop is not None and effective_stop < effective_from:
        raise ValidationError("effective_stop", "must be on or after effective_from")

    return ParsedIncome(
        name=name,
        quantity=quantity,
        recurrence=recurrence,
        effective_from=effective_from,
        effective_stop=effective_stop,
    )


def _parse_recurrence(raw: str) -> Recurrence:
    code = raw.strip()
    if not code:
        raise ValidationError("recurrence", "is required")
    try:
        return Recurrence.from_code(code)
    except ValueError as exc:
        raise ValidationError("recurrence", str(exc)) from exc


def _parse_required_date(raw: str, field: str) -> date:
    text = raw.strip()
    if not text:
        raise ValidationError(field, "is required")
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValidationError(field, "must be a valid date (YYYY-MM-DD)") from exc


def _parse_optional_date(raw: str, field: str) -> date | None:
    text = raw.strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValidationError(field, "must be a valid date (YYYY-MM-DD)") from exc
