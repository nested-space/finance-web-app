"""Income blueprint.

Lists income streams and supports create/delete via POST-redirect-GET. Calls
``IncomeService`` only. (Income exceptions have no UI in v1.0.0 — see D-011.)
"""

from __future__ import annotations

from flask import Blueprint, redirect, render_template, request, url_for
from flask.typing import ResponseReturnValue

from finance_web_app.core.contracts.errors import ValidationError
from finance_web_app.core.runtime.container import get_income_service
from finance_web_app.web.forms.income_form import parse_income_form
from finance_web_app.web.rendering.template_context import incomes_page_context

bp = Blueprint("income", __name__, url_prefix="/finance/income")


@bp.get("")
def list_income() -> str:
    context = incomes_page_context(get_income_service().list_all())
    return render_template("income.html", **context)


@bp.post("")
def create_income() -> ResponseReturnValue:
    service = get_income_service()
    try:
        parsed = parse_income_form(request.form)
        service.create(
            name=parsed.name,
            quantity=parsed.quantity,
            recurrence=parsed.recurrence,
            effective_from=parsed.effective_from,
            effective_stop=parsed.effective_stop,
        )
    except ValidationError as exc:
        context = incomes_page_context(service.list_all())
        return render_template("income.html", error=f"{exc.field}: {exc.reason}", **context), 400
    return redirect(url_for("income.list_income"))


@bp.post("/<int:income_id>/delete")
def delete_income(income_id: int) -> ResponseReturnValue:
    get_income_service().delete(income_id)
    return redirect(url_for("income.list_income"))
