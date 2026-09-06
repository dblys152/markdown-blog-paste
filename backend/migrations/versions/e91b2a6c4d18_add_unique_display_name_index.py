"""add unique display name index

Revision ID: e91b2a6c4d18
Revises: c4e91d7ab302
Create Date: 2026-09-06 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e91b2a6c4d18"
down_revision: str | Sequence[str] | None = "c4e91d7ab302"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "uq_users_display_name_lower",
        "users",
        [sa.text("lower(display_name)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_users_display_name_lower", table_name="users")
