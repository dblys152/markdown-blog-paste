"""scope login failures to existing users

Revision ID: e4c5f8a12d60
Revises: d2a6c8e41f93
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e4c5f8a12d60"
down_revision: str | Sequence[str] | None = "d2a6c8e41f93"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # The old rows are short-lived counters keyed by hashed email; they cannot
    # be mapped to users without the application HMAC key, so start fresh.
    op.create_table(
        "login_failure_states",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("failure_count", sa.Integer(), nullable=False),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("blocked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_login_failure_states_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", name=op.f("pk_login_failure_states")),
    )
    op.drop_table("login_attempts")


def downgrade() -> None:
    op.create_table(
        "login_attempts",
        sa.Column("identifier_hash", sa.String(length=64), nullable=False),
        sa.Column("failure_count", sa.Integer(), nullable=False),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("blocked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("identifier_hash", name=op.f("pk_login_attempts")),
    )
    op.drop_table("login_failure_states")
