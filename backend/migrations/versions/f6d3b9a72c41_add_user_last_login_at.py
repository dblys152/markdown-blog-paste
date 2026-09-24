"""add last login timestamp to users

Revision ID: f6d3b9a72c41
Revises: e4c5f8a12d60
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f6d3b9a72c41"
down_revision: str | Sequence[str] | None = "e4c5f8a12d60"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "last_login_at")
