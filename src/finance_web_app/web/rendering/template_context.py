"""Presentation shaping for budget pages.

The single home for mapping domain values to display text -- in particular the
``Category`` -> label map, which is intentionally absent from the domain
(``docs/ARCHITECTURE.md`` -> "Domain value objects"). No business logic here.
"""

from __future__ import annotations

from finance_web_app.domain.records import (
    COMMITMENT_CATEGORIES,
    COMMITMENT_RECURRENCES,
    Budget,
    Category,
    Commitment,
    Expense,
    Income,
)
from finance_web_app.domain.recurrence import Recurrence

CATEGORY_LABELS: dict[Category, str] = {
    Category.OCCASIONAL: "Occasional",
    Category.GROCERIES: "Groceries",
    Category.CLOTHING: "Clothing",
    Category.ENTERTAINMENT: "Entertainment",
    Category.PETROL: "Petrol",
    Category.KIDS: "Kids",
    Category.CHRISTMAS: "Christmas",
}

RECURRENCE_LABELS: dict[Recurrence, str] = {
    Recurrence.DAILY: "Daily",
    Recurrence.WEEKLY: "Weekly",
    Recurrence.MONTHLY: "Monthly",
    Recurrence.QUARTERLY: "Quarterly",
    Recurrence.ANNUAL: "Annual",
    Recurrence.ONCE_ONLY: "Once Only",
}

LENGTH_UNIT_CHOICES: list[tuple[str, str]] = [
    ("DAYS", "Days"),
    ("WEEKS", "Weeks"),
    ("MONTHS", "Months"),
    ("YEARS", "Years"),
]


def category_choices() -> list[tuple[str, str]]:
    """(code, label) pairs for the category select, in enum order."""
    return [(category.name, CATEGORY_LABELS[category]) for category in Category]


def budgets_page_context(budgets: list[Budget]) -> dict[str, object]:
    """Shape the budgets list into the template context for ``budgets.html``."""
    return {
        "budgets": [_budget_row(budget) for budget in budgets],
        "category_choices": category_choices(),
    }


def _budget_row(budget: Budget) -> dict[str, object]:
    stop = budget.period.stop_date
    return {
        "id": budget.id,
        "name": budget.name,
        "quantity": str(budget.quantity),
        "category": CATEGORY_LABELS[budget.category],
        "effective_from": budget.period.from_date.isoformat(),
        "effective_stop": stop.isoformat() if stop is not None else "",
    }


def expenses_page_context(expenses: list[Expense]) -> dict[str, object]:
    """Shape the expenses list into the template context for ``expenses.html``."""
    return {
        "expenses": [_expense_row(expense) for expense in expenses],
        "category_choices": category_choices(),
    }


def _expense_row(expense: Expense) -> dict[str, object]:
    return {
        "id": expense.id,
        "name": expense.name,
        "quantity": str(expense.quantity),
        "category": CATEGORY_LABELS[expense.category],
        "date": expense.date.isoformat(),
        "description": expense.description or "",
    }


def commitment_category_choices() -> list[tuple[str, str]]:
    return [(c.name, CATEGORY_LABELS[c]) for c in COMMITMENT_CATEGORIES]


def commitment_recurrence_choices() -> list[tuple[str, str]]:
    return [(r.name, RECURRENCE_LABELS[r]) for r in COMMITMENT_RECURRENCES]


def commitments_page_context(commitments: list[Commitment]) -> dict[str, object]:
    """Shape commitments into the template context, grouped by recurrence."""
    by_recurrence: dict[Recurrence, list[Commitment]] = {}
    for commitment in commitments:
        by_recurrence.setdefault(commitment.recurrence, []).append(commitment)

    groups = [
        {
            "recurrence": RECURRENCE_LABELS[recurrence],
            "commitments": [_commitment_row(c) for c in by_recurrence[recurrence]],
        }
        for recurrence in COMMITMENT_RECURRENCES
        if recurrence in by_recurrence
    ]
    return {
        "groups": groups,
        "category_choices": commitment_category_choices(),
        "recurrence_choices": commitment_recurrence_choices(),
        "length_unit_choices": LENGTH_UNIT_CHOICES,
    }


def _commitment_row(commitment: Commitment) -> dict[str, object]:
    return {
        "id": commitment.id,
        "name": commitment.name,
        "quantity": str(commitment.quantity),
        "category": CATEGORY_LABELS[commitment.category],
        "recurrence": RECURRENCE_LABELS[commitment.recurrence],
        "effective_from": commitment.period.from_date.isoformat(),
        "effective_stop": commitment.period.stop_date.isoformat()
        if commitment.period.stop_date is not None
        else "",
    }


def income_recurrence_choices() -> list[tuple[str, str]]:
    """(code, label) for the income recurrence select — all six patterns."""
    return [(recurrence.name, RECURRENCE_LABELS[recurrence]) for recurrence in Recurrence]


def incomes_page_context(incomes: list[Income]) -> dict[str, object]:
    """Shape the income list into the template context for ``income.html``."""
    return {
        "incomes": [_income_row(income) for income in incomes],
        "recurrence_choices": income_recurrence_choices(),
    }


def _income_row(income: Income) -> dict[str, object]:
    stop = income.period.stop_date
    return {
        "id": income.id,
        "name": income.name,
        "quantity": str(income.quantity),
        "recurrence": RECURRENCE_LABELS[income.recurrence],
        "effective_from": income.period.from_date.isoformat(),
        "effective_stop": stop.isoformat() if stop is not None else "",
    }
