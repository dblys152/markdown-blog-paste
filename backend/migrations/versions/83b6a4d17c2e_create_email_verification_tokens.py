"""create email verification tokens

Revision ID: 83b6a4d17c2e
Revises: 2e48a9c73d15
Create Date: 2026-08-27 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "83b6a4d17c2e"
down_revision: str | Sequence[str] | None = "2e48a9c73d15"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE users SET email_verified_at = now() WHERE email_verified_at IS NULL")
    op.create_table(
        "email_verification_tokens",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_email_verification_tokens_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_email_verification_tokens")),
        sa.UniqueConstraint(
            "token_hash",
            name=op.f("uq_email_verification_tokens_token_hash"),
        ),
    )
    op.create_index(
        op.f("ix_email_verification_tokens_user_id"),
        "email_verification_tokens",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_email_verification_tokens_user_id"),
        table_name="email_verification_tokens",
    )
    op.drop_table("email_verification_tokens")
