"""Contract test: commitment implementations satisfy the Protocol."""

from __future__ import annotations

import pytest
from sqlmodel import Session

from finance_web_app.core.contracts.commitment_repository import CommitmentRepository
from finance_web_app.infrastructure.persistence.commitment_repository import (
    SqlCommitmentRepository,
)

pytestmark = pytest.mark.unit


def test_sql_repository_satisfies_protocol(session: Session) -> None:
    assert isinstance(SqlCommitmentRepository(session), CommitmentRepository)


def test_fake_repository_satisfies_protocol(fake_commitment_repository: object) -> None:
    assert isinstance(fake_commitment_repository, CommitmentRepository)
