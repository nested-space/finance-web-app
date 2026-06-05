"""Presentation shaping for the resource pages.

The single home for mapping domain values to display text. Category names now
live in the ``category`` table, so the id->name map is built per request from the
category list rather than from a hardcoded label dict (``docs/ARCHITECTURE.md`` ->
"Domain value objects"). No business logic here.
"""

from __future__ import annotations

from finance_web_app.domain.records import (
    COMMITMENT_RECURRENCES,
    Budget,
    BudgetItem,
    Category,
    Commitment,
    Expense,
    Income,
)
from finance_web_app.domain.recurrence import Recurrence

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


def _name_map(categories: list[Category]) -> dict[int, str]:
    """id -> name lookup for resolving a record's ``category_id`` to display text."""
    return {category.id: category.name for category in categories if category.id is not None}


def category_choices(categories: list[Category]) -> list[tuple[str, str]]:
    """(id, name) pairs for a category select, in the categories' given order."""
    return [(str(category.id), category.name) for category in categories]


def categories_page_context(categories: list[Category]) -> dict[str, object]:
    """Shape the category list into the template context for ``categories.html``."""
    return {"categories": [{"id": c.id, "name": c.name} for c in categories]}


def _budget_item_choices(items: list[BudgetItem]) -> list[dict[str, object]]:
    """Item options carrying their ``category_id`` so the UI can filter by category."""
    return [{"id": item.id, "name": item.name, "category_id": item.category_id} for item in items]


def budgets_page_context(budgets: list[Budget], categories: list[Category]) -> dict[str, object]:
    """Shape the budgets list into the template context for ``budgets.html``."""
    names = _name_map(categories)
    return {
        "budgets": [_budget_row(budget, names) for budget in budgets],
        "category_choices": category_choices(categories),
    }


def budget_detail_context(
    budget: Budget, categories: list[Category], items: list[BudgetItem]
) -> dict[str, object]:
    """Shape a single budget and its category's items for ``budget_detail.html``."""
    names = _name_map(categories)
    return {
        "budget": _budget_row(budget, names),
        "budget_items": [{"id": item.id, "name": item.name} for item in items],
    }


def _budget_row(budget: Budget, names: dict[int, str]) -> dict[str, object]:
    stop = budget.period.stop_date
    return {
        "id": budget.id,
        "quantity": str(budget.quantity),
        "category": names.get(budget.category_id, ""),
        "effective_from": budget.period.from_date.isoformat(),
        "effective_stop": stop.isoformat() if stop is not None else "",
    }


def expenses_page_context(
    expenses: list[Expense], categories: list[Category], items: list[BudgetItem]
) -> dict[str, object]:
    """Shape the expenses list into the template context for ``expenses.html``."""
    cat_names = _name_map(categories)
    item_names = {item.id: item.name for item in items if item.id is not None}
    return {
        "expenses": [_expense_row(expense, cat_names, item_names) for expense in expenses],
        "category_choices": category_choices(categories),
        "budget_item_choices": _budget_item_choices(items),
    }


def _expense_row(
    expense: Expense, cat_names: dict[int, str], item_names: dict[int, str]
) -> dict[str, object]:
    return {
        "id": expense.id,
        "name": expense.name,
        "quantity": str(expense.quantity),
        "category": cat_names.get(expense.category_id, ""),
        "budget_item": (
            item_names.get(expense.budget_item_id, "") if expense.budget_item_id is not None else ""
        ),
        "date": expense.date.isoformat(),
        "description": expense.description or "",
    }


def commitment_recurrence_choices() -> list[tuple[str, str]]:
    return [(r.name, RECURRENCE_LABELS[r]) for r in COMMITMENT_RECURRENCES]


def commitments_page_context(
    commitments: list[Commitment], categories: list[Category]
) -> dict[str, object]:
    """Shape commitments into the template context, grouped by recurrence."""
    names = _name_map(categories)
    by_recurrence: dict[Recurrence, list[Commitment]] = {}
    for commitment in commitments:
        by_recurrence.setdefault(commitment.recurrence, []).append(commitment)

    groups = [
        {
            "recurrence": RECURRENCE_LABELS[recurrence],
            "commitments": [_commitment_row(c, names) for c in by_recurrence[recurrence]],
        }
        for recurrence in COMMITMENT_RECURRENCES
        if recurrence in by_recurrence
    ]
    return {
        "groups": groups,
        "category_choices": category_choices(categories),
        "recurrence_choices": commitment_recurrence_choices(),
        "length_unit_choices": LENGTH_UNIT_CHOICES,
    }


def _commitment_row(commitment: Commitment, names: dict[int, str]) -> dict[str, object]:
    return {
        "id": commitment.id,
        "name": commitment.name,
        "quantity": str(commitment.quantity),
        "category": names.get(commitment.category_id, ""),
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
