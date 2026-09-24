"""unify email verification and password reset tokens

Revision ID: d2a6c8e41f93
Revises: b7f4c2d91e60
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d2a6c8e41f93"
down_revision: str | Sequence[str] | None = "b7f4c2d91e60"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "account_confirmation_tokens",
        sa.Column("id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("purpose", sa.String(length=30), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_account_confirmation_tokens_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_account_confirmation_tokens")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_account_confirmation_tokens_token_hash")),
        sa.CheckConstraint(
            "purpose IN ('email_verification', 'password_reset')",
            name=op.f("ck_account_confirmation_tokens_purpose"),
        ),
    )
    op.create_index(
        op.f("ix_account_confirmation_tokens_user_id"), "account_confirmation_tokens", ["user_id"]
    )
    op.create_index(
        op.f("ix_account_confirmation_tokens_purpose"), "account_confirmation_tokens", ["purpose"]
    )

    for table, purpose in (
        ("email_verification_tokens", "email_verification"),
        ("password_reset_tokens", "password_reset"),
    ):
        op.execute(
            f"INSERT INTO account_confirmation_tokens "  # noqa: S608
            "(id, user_id, purpose, token_hash, expires_at, used_at, revoked_at, created_at) "
            f"SELECT id, user_id, '{purpose}', token_hash, expires_at, used_at, revoked_at, "
            f"created_at FROM {table}"
        )

    op.drop_table("email_verification_tokens")
    op.drop_table("password_reset_tokens")


def downgrade() -> None:
    for table, purpose in (
        ("email_verification_tokens", "email_verification"),
        ("password_reset_tokens", "password_reset"),
    ):
        op.create_table(
            table,
            sa.Column("id", sa.BigInteger(), autoincrement=False, nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.id"],
                name=op.f(f"fk_{table}_user_id_users"),
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id", name=op.f(f"pk_{table}")),
            sa.UniqueConstraint("token_hash", name=op.f(f"uq_{table}_token_hash")),
        )
        op.create_index(op.f(f"ix_{table}_user_id"), table, ["user_id"])
        op.execute(
            f"INSERT INTO {table} "  # noqa: S608
            "(id, user_id, token_hash, expires_at, used_at, revoked_at, created_at) "
            "SELECT id, user_id, token_hash, expires_at, used_at, revoked_at, created_at "
            f"FROM account_confirmation_tokens WHERE purpose = '{purpose}'"
        )

    op.drop_table("account_confirmation_tokens")
