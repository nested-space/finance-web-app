"""Commitment use cases."""

from __future__ import annotations

from datetime import date

from finance_web_app.core.contracts.category_repository import CategoryRepository
from finance_web_app.core.contracts.commitment_repository import CommitmentRepository
from finance_web_app.core.contracts.errors import NotFoundError, ValidationError
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import Commitment
from finance_web_app.domain.recurrence import Recurrence


class CommitmentService:
    def __init__(self, commitments: CommitmentRepository, categories: CategoryRepository) -> None:
        self._commitments = commitments
        self._categories = categories

    def list_all(self) -> list[Commitment]:
        return self._commitments.list_all()

    def list_effective(self, year: int, month: int) -> list[Commitment]:
        return self._commitments.list_effective(year, month)

    def totals_by_category(self, year: int, month: int) -> dict[int, Money]:
        """Sum the month's commitment amounts per category id (for the by-category pie)."""
        totals: dict[int, int] = {}
        for commitment in self._commitments.list_effective(year, month):
            totals[commitment.category_id] = (
                totals.get(commitment.category_id, 0) + commitment.quantity.pence()
            )
        return {category_id: Money.from_pence(pence) for category_id, pence in totals.items()}

    def create(
        self,
        *,
        name: str,
        quantity: Money,
        category_id: int,
        recurrence: Recurrence,
        effective_from: date,
        effective_stop: date,
    ) -> Commitment:
        if not name:
            raise ValidationError("name", "must be non-empty")
        try:
            self._categories.get(category_id)
        except NotFoundError:
            raise ValidationError("category", "does not exist") from None
        record = Commitment(
            name=name,
            quantity=quantity,
            category_id=category_id,
            recurrence=recurrence,
            effective_from=effective_from,
            effective_stop=effective_stop,
        )
        return self._commitments.create(record)

    def delete(self, commitment_id: int) -> None:
        self._commitments.delete(commitment_id)
