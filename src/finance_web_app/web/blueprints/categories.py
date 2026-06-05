"""Categories blueprint.

Manages the user-managed category list via POST-redirect-GET. Calls
``CategoryService`` only. Creating a duplicate name or deleting a category still
in use raises a ``ValidationError`` that re-renders the page with HTTP 400
(``docs/ARCHITECTURE.md`` -> "Runtime flow").
"""

from __future__ import annotations

from flask import Blueprint, redirect, render_template, request, url_for
from flask.typing import ResponseReturnValue

from finance_web_app.core.contracts.errors import ValidationError
from finance_web_app.core.runtime.container import get_category_service
from finance_web_app.web.forms.category_form import parse_category_form
from finance_web_app.web.rendering.template_context import categories_page_context

bp = Blueprint("categories", __name__, url_prefix="/finance/categories")


@bp.get("")
def list_categories() -> str:
    context = categories_page_context(get_category_service().list_all())
    return render_template("categories.html", **context)


@bp.post("")
def create_category() -> ResponseReturnValue:
    service = get_category_service()
    try:
        parsed = parse_category_form(request.form)
        service.create(name=parsed.name)
    except ValidationError as exc:
        context = categories_page_context(service.list_all())
        return render_template(
            "categories.html", error=f"{exc.field}: {exc.reason}", **context
        ), 400
    return redirect(url_for("categories.list_categories"))


@bp.post("/<int:category_id>/delete")
def delete_category(category_id: int) -> ResponseReturnValue:
    service = get_category_service()
    try:
        service.delete(category_id)
    except ValidationError as exc:
        context = categories_page_context(service.list_all())
        return render_template(
            "categories.html", error=f"{exc.field}: {exc.reason}", **context
        ), 400
    return redirect(url_for("categories.list_categories"))
