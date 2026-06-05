"""Category form parsing and validation.

Only a name is collected; uniqueness and the in-use deletion guard live in the
service. Depends only on the contract errors (``docs/ARCHITECTURE.md`` -> "Layer
map").
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from finance_web_app.core.contracts.errors import ValidationError


@dataclass(frozen=True)
class ParsedCategory:
    name: str


def parse_category_form(form: Mapping[str, str]) -> ParsedCategory:
    name = form.get("name", "").strip()
    if not name:
        raise ValidationError("name", "is required")
    return ParsedCategory(name=name)
