"""Dependency wiring -- the one seam that binds concrete repositories to services.

The only module permitted to import both a contract Protocol's concrete
implementation and the service that consumes it. It also owns the request-scoped
SQLModel ``Session`` stored on Flask's ``g`` (``docs/ARCHITECTURE.md`` -> "Layer
map", "Runtime flow"). Plain factory wiring -- not a DI framework.
"""

from __future__ import annotations

from flask import current_app, g
from sqlmodel import Session

from finance_web_app.application.services.budget_service import BudgetService
from finance_web_app.application.services.commitment_service import CommitmentService
from finance_web_app.application.services.expense_service import ExpenseService
from finance_web_app.application.services.finance_model_service import FinanceModelService
from finance_web_app.application.services.history_service import HistoryService
from finance_web_app.application.services.income_service import IncomeService
from finance_web_app.application.services.insights_service import InsightsService
from finance_web_app.infrastructure.persistence.budget_repository import SqlBudgetRepository
from finance_web_app.infrastructure.persistence.commitment_repository import SqlCommitmentRepository
from finance_web_app.infrastructure.persistence.engine import make_session
from finance_web_app.infrastructure.persistence.expense_repository import SqlExpenseRepository
from finance_web_app.infrastructure.persistence.income_repository import SqlIncomeRepository


def get_session() -> Session:
    """Return the request-scoped session, opening it on first use."""
    if "db_session" not in g:
        g.db_session = make_session(current_app.config["DB_ENGINE"])
    session: Session = g.db_session
    return session


def close_session(_exception: BaseException | None = None) -> None:
    """Teardown hook: close the request-scoped session if one was opened."""
    session = g.pop("db_session", None)
    if session is not None:
        session.close()


def get_budget_service() -> BudgetService:
    return BudgetService(SqlBudgetRepository(get_session()))


def get_expense_service() -> ExpenseService:
    return ExpenseService(SqlExpenseRepository(get_session()))


def get_commitment_service() -> CommitmentService:
    return CommitmentService(SqlCommitmentRepository(get_session()))


def get_income_service() -> IncomeService:
    return IncomeService(SqlIncomeRepository(get_session()))


def get_finance_model_service() -> FinanceModelService:
    session = get_session()
    return FinanceModelService(
        SqlIncomeRepository(session),
        SqlCommitmentRepository(session),
        SqlExpenseRepository(session),
        SqlBudgetRepository(session),
    )


def get_insights_service() -> InsightsService:
    session = get_session()
    return InsightsService(
        get_finance_model_service(),
        SqlExpenseRepository(session),
        SqlBudgetRepository(session),
    )


def get_history_service() -> HistoryService:
    return HistoryService(get_budget_service(), get_expense_service())
