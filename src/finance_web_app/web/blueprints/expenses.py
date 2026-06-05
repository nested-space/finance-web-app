"""Expenses blueprint.

Lists the current month's expenses (the stricter date predicate) and supports
create/delete via POST-redirect-GET. Calls ``ExpenseService`` only.
"""

from __future__ import annotations

from datetime import date

from flask import Blueprint, redirect, render_template, request, url_for
from flask.typing import ResponseReturnValue

from finance_web_app.core.contracts.errors import ValidationError
from finance_web_app.core.runtime.container import (
    get_budget_item_service,
    get_budget_service,
    get_category_service,
    get_expense_service,
    get_history_service,
)
from finance_web_app.web.forms.expense_form import parse_expense_form
from finance_web_app.web.rendering.json_response import (
    expenses_charts_payload,
    expenses_curve_payload,
)
from finance_web_app.web.rendering.template_context import expenses_page_context

bp = Blueprint("expenses", __name__, url_prefix="/finance/expenses")


def _current_month_context() -> dict[str, object]:
    today = date.today()
    expense_service = get_expense_service()
    categories = get_category_service().list_all()
    context = expenses_page_context(
        expense_service.list_effective(today.year, today.month),
        categories,
        get_budget_item_service().list_all(),
    )
    curve = expenses_curve_payload(
        expense_service.cumulative_spend(today.year, today.month, None),
        get_budget_service().cumulative_allocation(today.year, today.month, None),
    )
    context["charts"] = expenses_charts_payload(
        today.year,
        today.month,
        curve,
        expense_service.totals_by_category(today.year, today.month),
        get_history_service().expense_history(today.year, today.month),
        categories,
    )
    return context


@bp.get("")
def list_expenses() -> str:
    return render_template("expenses.html", **_current_month_context())


@bp.post("")
def create_expense() -> ResponseReturnValue:
    try:
        parsed = parse_expense_form(request.form)
        get_expense_service().create(
            name=parsed.name,
            quantity=parsed.quantity,
            category_id=parsed.category_id,
            budget_item_id=parsed.budget_item_id,
            date=parsed.date,
            description=parsed.description,
        )
    except ValidationError as exc:
        return render_template(
            "expenses.html", error=f"{exc.field}: {exc.reason}", **_current_month_context()
        ), 400
    return redirect(url_for("expenses.list_expenses"))


@bp.post("/<int:expense_id>/delete")
def delete_expense(expense_id: int) -> ResponseReturnValue:
    get_expense_service().delete(expense_id)
    return redirect(url_for("expenses.list_expenses"))
