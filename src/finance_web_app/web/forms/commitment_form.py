"""Commitment form parsing and validation.

Computes ``effective_stop`` from ``length`` + ``length_unit`` (or collapses to a
single day for ``ONCE_ONLY``), and enforces the commitment category/recurrence
subsets against the single source in ``domain.records``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, timedelta

from finance_web_app.core.contracts.errors import ValidationError
from finance_web_app.domain.calendar_math import add_months, add_years
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import COMMITMENT_CATEGORIES, COMMITMENT_RECURRENCES, Category
from finance_web_app.domain.recurrence import Recurrence

_LENGTH_UNITS = ("DAYS", "WEEKS", "MONTHS", "YEARS")


@dataclass(frozen=True)
class ParsedCommitment:
    name: str
    quantity: Money
    category: Category
    recurrence: Recurrence
    effective_from: date
    effective_stop: date


def parse_commitment_form(form: Mapping[str, str]) -> ParsedCommitment:
    name = form.get("name", "").strip()
    if not name:
        raise ValidationError("name", "is required")

    try:
        quantity = Money.from_form_string(form.get("quantity", ""))
    except ValueError as exc:
        raise ValidationError("quantity", str(exc)) from exc

    category = _parse_subset_category(form.get("category", ""))
    recurrence = _parse_subset_recurrence(form.get("recurrence", ""))
    effective_from = _parse_required_date(form.get("effective_from", ""), "effective_from")

    if recurrence is Recurrence.ONCE_ONLY:
        effective_stop = effective_from
    else:
        length = _parse_positive_int(form.get("length", ""), "length")
        unit = _parse_length_unit(form.get("length_unit", ""))
        effective_stop = _apply_length(effective_from, length, unit)

    return ParsedCommitment(
        name=name,
        quantity=quantity,
        category=category,
        recurrence=recurrence,
        effective_from=effective_from,
        effective_stop=effective_stop,
    )


def _parse_subset_category(raw: str) -> Category:
    code = raw.strip()
    if not code:
        raise ValidationError("category", "is required")
    try:
        category = Category.from_code(code)
    except ValueError as exc:
        raise ValidationError("category", str(exc)) from exc
    if category not in COMMITMENT_CATEGORIES:
        raise ValidationError("category", f"{code} is not valid for commitments")
    return category


def _parse_subset_recurrence(raw: str) -> Recurrence:
    code = raw.strip()
    if not code:
        raise ValidationError("recurrence", "is required")
    try:
        recurrence = Recurrence.from_code(code)
    except ValueError as exc:
        raise ValidationError("recurrence", str(exc)) from exc
    if recurrence not in COMMITMENT_RECURRENCES:
        raise ValidationError("recurrence", f"{code} is not valid for commitments")
    return recurrence


def _parse_required_date(raw: str, field: str) -> date:
    text = raw.strip()
    if not text:
        raise ValidationError(field, "is required")
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValidationError(field, "must be a valid date (YYYY-MM-DD)") from exc


def _parse_positive_int(raw: str, field: str) -> int:
    text = raw.strip()
    if not text:
        raise ValidationError(field, "is required")
    try:
        value = int(text)
    except ValueError as exc:
        raise ValidationError(field, "must be a whole number") from exc
    if value < 1:
        raise ValidationError(field, "must be at least 1")
    return value


def _parse_length_unit(raw: str) -> str:
    code = raw.strip().upper()
    if code not in _LENGTH_UNITS:
        raise ValidationError("length_unit", "must be one of Days, Weeks, Months, Years")
    return code


def _apply_length(start: date, length: int, unit: str) -> date:
    if unit == "DAYS":
        return start + timedelta(days=length)
    if unit == "WEEKS":
        return start + timedelta(weeks=length)
    if unit == "MONTHS":
        return add_months(start, length)
    if unit == "YEARS":
        return add_years(start, length)
    raise AssertionError(f"unhandled length unit: {unit!r}")
