"""Budgets blueprint.

Parses the request, calls ``BudgetService``, and decides redirect vs. render.
It never touches a repository directly. Create and delete use POST-redirect-GET;
a ``ValidationError`` re-renders the page with a message and HTTP 400
(``docs/ARCHITECTURE.md`` -> "Runtime flow"). The page also embeds the current
month's chart payload.
"""

from __future__ import annotations

from datetime import date

from flask import Blueprint, redirect, render_template, request, url_for
from flask.typing import ResponseReturnValue

from finance_web_app.core.contracts.errors import ValidationError
from finance_web_app.core.runtime.container import (
    get_budget_service,
    get_expense_service,
    get_history_service,
)
from finance_web_app.web.forms.budget_form import parse_budget_form
from finance_web_app.web.rendering.json_response import budgets_charts_payload
from finance_web_app.web.rendering.template_context import budgets_page_context

bp = Blueprint("budgets", __name__, url_prefix="/finance/budgets")


def _page_context() -> dict[str, object]:
    today = date.today()
    budget_service = get_budget_service()
    context = budgets_page_context(budget_service.list_all())
    context["charts"] = budgets_charts_payload(
        get_expense_service().totals_by_category(today.year, today.month),
        budget_service.totals_by_category(today.year, today.month),
        get_history_service().budget_history(today.year, today.month),
    )
    return context


@bp.get("")
def list_budgets() -> str:
    return render_template("budgets.html", **_page_context())


@bp.post("")
def create_budget() -> ResponseReturnValue:
    try:
        parsed = parse_budget_form(request.form)
        get_budget_service().create(
            name=parsed.name,
            quantity=parsed.quantity,
            category=parsed.category,
            period=parsed.period,
        )
    except ValidationError as exc:
        return render_template(
            "budgets.html", error=f"{exc.field}: {exc.reason}", **_page_context()
        ), 400
    return redirect(url_for("budgets.list_budgets"))


@bp.post("/<int:budget_id>/delete")
def delete_budget(budget_id: int) -> ResponseReturnValue:
    get_budget_service().delete(budget_id)
    return redirect(url_for("budgets.list_budgets"))
