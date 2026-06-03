"""Budgets blueprint.

Parses the request, calls ``BudgetService``, and decides redirect vs. render.
It never touches a repository directly. Create and delete use POST-redirect-GET;
a ``ValidationError`` re-renders the page with a message and HTTP 400
(``docs/ARCHITECTURE.md`` -> "Runtime flow").
"""

from __future__ import annotations

from flask import Blueprint, redirect, render_template, request, url_for
from flask.typing import ResponseReturnValue

from finance_web_app.core.contracts.errors import ValidationError
from finance_web_app.core.runtime.container import get_budget_service
from finance_web_app.web.forms.budget_form import parse_budget_form
from finance_web_app.web.rendering.template_context import budgets_page_context

bp = Blueprint("budgets", __name__, url_prefix="/finance/budgets")


@bp.get("")
def list_budgets() -> str:
    service = get_budget_service()
    context = budgets_page_context(service.list_all())
    return render_template("budgets.html", **context)


@bp.post("")
def create_budget() -> ResponseReturnValue:
    service = get_budget_service()
    try:
        parsed = parse_budget_form(request.form)
        service.create(
            name=parsed.name,
            quantity=parsed.quantity,
            category=parsed.category,
            period=parsed.period,
        )
    except ValidationError as exc:
        context = budgets_page_context(service.list_all())
        return render_template("budgets.html", error=f"{exc.field}: {exc.reason}", **context), 400
    return redirect(url_for("budgets.list_budgets"))


@bp.post("/<int:budget_id>/delete")
def delete_budget(budget_id: int) -> ResponseReturnValue:
    get_budget_service().delete(budget_id)
    return redirect(url_for("budgets.list_budgets"))
