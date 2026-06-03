"""Commitment use cases."""

from __future__ import annotations

from datetime import date

from finance_web_app.core.contracts.commitment_repository import CommitmentRepository
from finance_web_app.core.contracts.errors import ValidationError
from finance_web_app.domain.money import Money
from finance_web_app.domain.records import Category, Commitment
from finance_web_app.domain.recurrence import Recurrence


class CommitmentService:
    def __init__(self, commitments: CommitmentRepository) -> None:
        self._commitments = commitments

    def list_all(self) -> list[Commitment]:
        return self._commitments.list_all()

    def list_effective(self, year: int, month: int) -> list[Commitment]:
        return self._commitments.list_effective(year, month)

    def totals_by_category(self, year: int, month: int) -> dict[Category, Money]:
        """Sum the month's commitment amounts per category (for the by-category pie)."""
        totals: dict[Category, int] = {}
        for commitment in self._commitments.list_effective(year, month):
            totals[commitment.category] = (
                totals.get(commitment.category, 0) + commitment.quantity.pence()
            )
        return {category: Money.from_pence(pence) for category, pence in totals.items()}

    def create(
        self,
        *,
        name: str,
        quantity: Money,
        category: Category,
        recurrence: Recurrence,
        effective_from: date,
        effective_stop: date,
    ) -> Commitment:
        if not name:
            raise ValidationError("name", "must be non-empty")
        record = Commitment(
            name=name,
            quantity=quantity,
            category=category,
            recurrence=recurrence,
            effective_from=effective_from,
            effective_stop=effective_stop,
        )
        return self._commitments.create(record)

    def delete(self, commitment_id: int) -> None:
        self._commitments.delete(commitment_id)
