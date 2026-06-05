"""user managed categories budget items

Replaces the fixed ``Category`` enum with a user-managed ``category`` table shared
by budgets, budget items, expenses, and commitments; drops the per-resource
category CHECK sets (the foreign key enforces validity instead); moves the budget
amount to the category level (drops ``budget.name``); and adds ``budget_item`` plus
``expense.budget_item_id`` for sub-classification.

Data migration (best effort for existing rows; a no-op on a fresh database):
seeds the seven previously-fixed categories, backfills every row's ``category_id``
from its old enum code, and preserves each existing budget's ``name`` as a budget
item under the same category.

Revision ID: 61f25195c783
Revises: 601a6302441d
Create Date: 2026-06-05 09:52:16.631265

"""

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "61f25195c783"
down_revision: str | None = "601a6302441d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (old enum code -> display name) for the seven categories that were fixed before
# this migration. The display name becomes the user-managed category's name; the
# code is used only to backfill existing rows.
_CATEGORY_SEED: tuple[tuple[str, str], ...] = (
    ("OCCASIONAL", "Occasional"),
    ("GROCERIES", "Groceries"),
    ("CLOTHING", "Clothing"),
    ("ENTERTAINMENT", "Entertainment"),
    ("PETROL", "Petrol"),
    ("KIDS", "Kids"),
    ("CHRISTMAS", "Christmas"),
)


# One fixed UPDATE per table (no interpolation): map each old enum code to its
# seeded category id.
_BACKFILL_SQL: dict[str, str] = {
    "budget": "UPDATE budget SET category_id = :cid WHERE category = :code",
    "commitment": "UPDATE commitment SET category_id = :cid WHERE category = :code",
    "expense": "UPDATE expense SET category_id = :cid WHERE category = :code",
}


def _backfill_category_id(table: str, code_to_id: dict[str, int]) -> None:
    bind = op.get_bind()
    statement = sa.text(_BACKFILL_SQL[table])
    for code, category_id in code_to_id.items():
        bind.execute(statement, {"cid": category_id, "code": code})


def upgrade() -> None:
    op.create_table(
        "category",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.CheckConstraint("length(name) > 0", name="category_name_nonempty"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "budget_item",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.CheckConstraint("length(name) > 0", name="budget_item_name_nonempty"),
        sa.ForeignKeyConstraint(["category_id"], ["category.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Seed the previously-fixed categories and resolve each code to its new id.
    now = datetime.now(UTC)
    op.bulk_insert(
        sa.table(
            "category",
            sa.column("name", sa.String),
            sa.column("created", sa.DateTime),
        ),
        [{"name": label, "created": now} for _code, label in _CATEGORY_SEED],
    )
    bind = op.get_bind()
    label_to_id = {
        name: cid for cid, name in bind.execute(sa.text("SELECT id, name FROM category")).all()
    }
    code_to_id = {code: label_to_id[label] for code, label in _CATEGORY_SEED}

    # budget: backfill category_id, preserve each budget's name as a budget item,
    # then move the amount to the category level (drop name) and drop the old
    # enum column and its CHECK sets.
    op.add_column("budget", sa.Column("category_id", sa.Integer(), nullable=True))
    _backfill_category_id("budget", code_to_id)
    bind.execute(
        sa.text(
            "INSERT INTO budget_item (name, category_id, created) "
            "SELECT name, category_id, created FROM budget "
            "WHERE name IS NOT NULL AND category_id IS NOT NULL"
        )
    )
    with op.batch_alter_table("budget", schema=None) as batch_op:
        batch_op.alter_column("category_id", existing_type=sa.Integer(), nullable=False)
        batch_op.create_foreign_key("budget_category_fk", "category", ["category_id"], ["id"])
        batch_op.drop_constraint("budget_category_valid", type_="check")
        batch_op.drop_constraint("budget_name_nonempty", type_="check")
        batch_op.drop_column("name")
        batch_op.drop_column("category")

    op.add_column("commitment", sa.Column("category_id", sa.Integer(), nullable=True))
    _backfill_category_id("commitment", code_to_id)
    with op.batch_alter_table("commitment", schema=None) as batch_op:
        batch_op.alter_column("category_id", existing_type=sa.Integer(), nullable=False)
        batch_op.create_foreign_key("commitment_category_fk", "category", ["category_id"], ["id"])
        batch_op.drop_constraint("commitment_category_valid", type_="check")
        batch_op.drop_column("category")

    op.add_column("expense", sa.Column("category_id", sa.Integer(), nullable=True))
    op.add_column("expense", sa.Column("budget_item_id", sa.Integer(), nullable=True))
    _backfill_category_id("expense", code_to_id)
    with op.batch_alter_table("expense", schema=None) as batch_op:
        batch_op.alter_column("category_id", existing_type=sa.Integer(), nullable=False)
        batch_op.create_foreign_key("expense_category_fk", "category", ["category_id"], ["id"])
        batch_op.create_foreign_key(
            "expense_budget_item_fk",
            "budget_item",
            ["budget_item_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.drop_constraint("expense_category_valid", type_="check")
        batch_op.drop_column("category")


def downgrade() -> None:
    _category_check = (
        "category IN ('OCCASIONAL', 'GROCERIES', 'CLOTHING', "
        "'ENTERTAINMENT', 'PETROL', 'KIDS', 'CHRISTMAS')"
    )
    with op.batch_alter_table("expense", schema=None) as batch_op:
        batch_op.add_column(sa.Column("category", sa.VARCHAR(length=13), nullable=True))
        batch_op.drop_constraint("expense_category_fk", type_="foreignkey")
        batch_op.drop_constraint("expense_budget_item_fk", type_="foreignkey")
        batch_op.drop_column("budget_item_id")
        batch_op.drop_column("category_id")
        batch_op.create_check_constraint("expense_category_valid", _category_check)

    with op.batch_alter_table("commitment", schema=None) as batch_op:
        batch_op.add_column(sa.Column("category", sa.VARCHAR(length=13), nullable=True))
        batch_op.drop_constraint("commitment_category_fk", type_="foreignkey")
        batch_op.drop_column("category_id")
        batch_op.create_check_constraint("commitment_category_valid", _category_check)

    with op.batch_alter_table("budget", schema=None) as batch_op:
        batch_op.add_column(sa.Column("category", sa.VARCHAR(length=13), nullable=True))
        batch_op.add_column(sa.Column("name", sa.VARCHAR(), nullable=True))
        batch_op.drop_constraint("budget_category_fk", type_="foreignkey")
        batch_op.drop_column("category_id")
        batch_op.create_check_constraint("budget_category_valid", _category_check)
        batch_op.create_check_constraint("budget_name_nonempty", "length(name) > 0")

    op.drop_table("budget_item")
    op.drop_table("category")
