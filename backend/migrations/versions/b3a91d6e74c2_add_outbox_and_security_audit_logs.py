"""add outbox messages and security audit logs

Revision ID: b3a91d6e74c2
Revises: f6d3b9a72c41
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b3a91d6e74c2"
down_revision: str | Sequence[str] | None = "f6d3b9a72c41"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "outbox_messages",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("event_id", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("aggregate_id", sa.BigInteger(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_outbox_messages"),
        sa.UniqueConstraint("event_id", name="uq_outbox_messages_event_id"),
    )
    op.create_index("ix_outbox_messages_event_type", "outbox_messages", ["event_type"])
    op.create_index("ix_outbox_messages_aggregate_id", "outbox_messages", ["aggregate_id"])
    op.create_index("ix_outbox_messages_status", "outbox_messages", ["status"])
    op.create_index(
        "ix_outbox_messages_pending",
        "outbox_messages",
        ["status", "available_at"],
    )

    op.create_table(
        "security_audit_logs",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("event_id", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_security_audit_logs"),
        sa.UniqueConstraint("event_id", name="uq_security_audit_logs_event_id"),
    )
    op.create_index(
        "ix_security_audit_logs_event_type",
        "security_audit_logs",
        ["event_type"],
    )
    op.create_index("ix_security_audit_logs_user_id", "security_audit_logs", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_security_audit_logs_user_id", table_name="security_audit_logs")
    op.drop_index("ix_security_audit_logs_event_type", table_name="security_audit_logs")
    op.drop_table("security_audit_logs")

    op.drop_index("ix_outbox_messages_pending", table_name="outbox_messages")
    op.drop_index("ix_outbox_messages_status", table_name="outbox_messages")
    op.drop_index("ix_outbox_messages_aggregate_id", table_name="outbox_messages")
    op.drop_index("ix_outbox_messages_event_type", table_name="outbox_messages")
    op.drop_table("outbox_messages")
