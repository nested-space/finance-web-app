"""Presentation shaping for budget pages.

The single home for mapping domain values to display text -- in particular the
``Category`` -> label map, which is intentionally absent from the domain
(``docs/ARCHITECTURE.md`` -> "Domain value objects"). No business logic here.
"""

from __future__ import annotations

from finance_web_app.domain.records import Budget, Category, Expense

CATEGORY_LABELS: dict[Category, str] = {
    Category.OCCASIONAL: "Occasional",
    Category.GROCERIES: "Groceries",
    Category.CLOTHING: "Clothing",
    Category.ENTERTAINMENT: "Entertainment",
    Category.PETROL: "Petrol",
    Category.KIDS: "Kids",
    Category.CHRISTMAS: "Christmas",
}


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
