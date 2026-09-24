"""reconcile account confirmation token table name

Revision ID: f1a6c9d84e27
Revises: b3a91d6e74c2
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f1a6c9d84e27"
down_revision: str | Sequence[str] | None = "b3a91d6e74c2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LEGACY_TABLE = "auth_tokens"
CANONICAL_TABLE = "account_confirmation_tokens"


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    has_legacy_table = inspector.has_table(LEGACY_TABLE)
    has_canonical_table = inspector.has_table(CANONICAL_TABLE)

    if has_legacy_table and has_canonical_table:
        raise RuntimeError(
            f"Both {LEGACY_TABLE} and {CANONICAL_TABLE} exist; manual reconciliation is required"
        )
    if has_canonical_table:
        return
    if not has_legacy_table:
        raise RuntimeError(
            f"Neither {LEGACY_TABLE} nor {CANONICAL_TABLE} exists; "
            "the database schema does not match the migration history"
        )

    op.rename_table(LEGACY_TABLE, CANONICAL_TABLE)
    op.execute(
        sa.text(
            "ALTER TABLE account_confirmation_tokens "
            "RENAME CONSTRAINT pk_auth_tokens TO pk_account_confirmation_tokens"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE account_confirmation_tokens "
            "RENAME CONSTRAINT fk_auth_tokens_user_id_users "
            "TO fk_account_confirmation_tokens_user_id_users"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE account_confirmation_tokens "
            "RENAME CONSTRAINT uq_auth_tokens_token_hash "
            "TO uq_account_confirmation_tokens_token_hash"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE account_confirmation_tokens "
            "RENAME CONSTRAINT ck_auth_tokens_purpose "
            "TO ck_account_confirmation_tokens_purpose"
        )
    )
    op.execute(
        sa.text(
            "ALTER INDEX ix_auth_tokens_user_id RENAME TO ix_account_confirmation_tokens_user_id"
        )
    )
    op.execute(
        sa.text(
            "ALTER INDEX ix_auth_tokens_purpose RENAME TO ix_account_confirmation_tokens_purpose"
        )
    )


def downgrade() -> None:
    # The preceding revision already defines the canonical table name. This migration repairs
    # databases that had applied an earlier local definition under the legacy name, so reverting
    # the repair would recreate schema drift instead of restoring the preceding revision.
    pass
