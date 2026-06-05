"""Unit tests for category form parsing/validation."""

from __future__ import annotations

import pytest

from finance_web_app.core.contracts.errors import ValidationError
from finance_web_app.web.forms.category_form import parse_category_form

pytestmark = pytest.mark.unit


def test_valid_form_trims_name() -> None:
    assert parse_category_form({"name": "  Holidays  "}).name == "Holidays"


@pytest.mark.parametrize("bad", ["", "   "])
def test_blank_name_is_rejected(bad: str) -> None:
    with pytest.raises(ValidationError) as exc:
        parse_category_form({"name": bad})
    assert exc.value.field == "name"
