"""rename page position to sort order

Revision ID: 7a31d9e4c2f8
Revises: 4b8c2f90e1a7
Create Date: 2026-08-22 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "7a31d9e4c2f8"
down_revision: str | Sequence[str] | None = "4b8c2f90e1a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("ix_pages_owner_parent_position", table_name="pages")
    op.alter_column("pages", "position", new_column_name="sort_order")
    op.create_index(
        "ix_pages_owner_parent_sort_order",
        "pages",
        ["owner_id", "parent_id", "sort_order"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_pages_owner_parent_sort_order", table_name="pages")
    op.alter_column("pages", "sort_order", new_column_name="position")
    op.create_index(
        "ix_pages_owner_parent_position",
        "pages",
        ["owner_id", "parent_id", "position"],
        unique=False,
    )
