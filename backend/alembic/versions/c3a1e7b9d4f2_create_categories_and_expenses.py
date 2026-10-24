"""create categories and expenses

Revision ID: c3a1e7b9d4f2
Revises:
Create Date: 2026-10-25 02:09:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c3a1e7b9d4f2"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PREDEFINED_CATEGORIES = (
    "Food",
    "Transport",
    "Housing",
    "Utilities",
    "Healthcare",
    "Entertainment",
    "Other",
)


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column(
            "is_predefined",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.create_index(
        "uq_categories_name_lower",
        "categories",
        [sa.text("lower(name)")],
        unique=True,
    )
    categories = sa.table(
        "categories",
        sa.column("name", sa.String),
        sa.column("is_predefined", sa.Boolean),
    )
    op.bulk_insert(
        categories,
        [
            {"name": name, "is_predefined": True}
            for name in PREDEFINED_CATEGORIES
        ],
    )
    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("expense_date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column(
            "category_id",
            sa.Integer(),
            sa.ForeignKey("categories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.CheckConstraint("amount > 0", name="ck_expenses_amount_positive"),
    )
    op.create_index("ix_expenses_category_id", "expenses", ["category_id"])
    op.create_index("ix_expenses_expense_date", "expenses", ["expense_date"])


def downgrade() -> None:
    op.drop_index("ix_expenses_expense_date", table_name="expenses")
    op.drop_index("ix_expenses_category_id", table_name="expenses")
    op.drop_table("expenses")
    op.drop_index("uq_categories_name_lower", table_name="categories")
    op.drop_table("categories")
