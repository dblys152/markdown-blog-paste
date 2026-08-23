"""add page deleted at

Revision ID: 2e48a9c73d15
Revises: 7a31d9e4c2f8
Create Date: 2026-08-22 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "2e48a9c73d15"
down_revision: str | Sequence[str] | None = "7a31d9e4c2f8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "pages",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_pages_deleted_at", "pages", ["deleted_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_pages_deleted_at", table_name="pages")
    op.drop_column("pages", "deleted_at")
