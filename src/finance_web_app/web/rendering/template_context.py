"""Presentation shaping for budget pages.

The single home for mapping domain values to display text -- in particular the
``Category`` -> label map, which is intentionally absent from the domain
(``docs/ARCHITECTURE.md`` -> "Domain value objects"). No business logic here.
"""

from __future__ import annotations

from finance_web_app.domain.records import BudgetRecord, Category

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


def budgets_page_context(budgets: list[BudgetRecord]) -> dict[str, object]:
    """Shape the budgets list into the template context for ``budgets.html``."""
    return {
        "budgets": [_budget_row(budget) for budget in budgets],
        "category_choices": category_choices(),
    }


def _budget_row(budget: BudgetRecord) -> dict[str, object]:
    stop = budget.period.stop_date
    return {
        "id": budget.id,
        "name": budget.name,
        "quantity": str(budget.quantity),
        "category": CATEGORY_LABELS[budget.category],
        "effective_from": budget.period.from_date.isoformat(),
        "effective_stop": stop.isoformat() if stop is not None else "",
    }
