"""Commitments blueprint.

Lists commitments grouped by recurrence and supports create/delete via
POST-redirect-GET. Calls ``CommitmentService`` only.
"""

from __future__ import annotations

from flask import Blueprint, redirect, render_template, request, url_for
from flask.typing import ResponseReturnValue

from finance_web_app.core.contracts.errors import ValidationError
from finance_web_app.core.runtime.container import get_commitment_service
from finance_web_app.web.forms.commitment_form import parse_commitment_form
from finance_web_app.web.rendering.template_context import commitments_page_context

bp = Blueprint("commitments", __name__, url_prefix="/finance/commitments")


@bp.get("")
def list_commitments() -> str:
    context = commitments_page_context(get_commitment_service().list_all())
    return render_template("commitments.html", **context)


@bp.post("")
def create_commitment() -> ResponseReturnValue:
    service = get_commitment_service()
    try:
        parsed = parse_commitment_form(request.form)
        service.create(
            name=parsed.name,
            quantity=parsed.quantity,
            category=parsed.category,
            recurrence=parsed.recurrence,
            effective_from=parsed.effective_from,
            effective_stop=parsed.effective_stop,
        )
    except ValidationError as exc:
        context = commitments_page_context(service.list_all())
        return render_template(
            "commitments.html", error=f"{exc.field}: {exc.reason}", **context
        ), 400
    return redirect(url_for("commitments.list_commitments"))


@bp.post("/<int:commitment_id>/delete")
def delete_commitment(commitment_id: int) -> ResponseReturnValue:
    get_commitment_service().delete(commitment_id)
    return redirect(url_for("commitments.list_commitments"))
