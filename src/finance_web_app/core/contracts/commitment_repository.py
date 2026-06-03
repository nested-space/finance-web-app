"""Commitment repository contract."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from finance_web_app.domain.records import Commitment


@runtime_checkable
class CommitmentRepository(Protocol):
    def list_all(self) -> list[Commitment]: ...

    def list_effective(self, year: int, month: int) -> list[Commitment]: ...

    def get(self, commitment_id: int) -> Commitment:
        """Return one commitment. Raises ``NotFoundError`` if absent."""
        ...

    def create(self, record: Commitment) -> Commitment:
        """Persist a new commitment, returning it with ``id`` set."""
        ...

    def delete(self, commitment_id: int) -> None:
        """Delete a commitment. Raises ``NotFoundError`` if absent."""
        ...
