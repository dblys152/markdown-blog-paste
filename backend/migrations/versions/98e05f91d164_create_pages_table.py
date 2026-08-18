"""create pages table

Revision ID: 98e05f91d164
Revises: 7daeccd99a53
Create Date: 2026-08-18 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "98e05f91d164"
down_revision: str | Sequence[str] | None = "7daeccd99a53"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pages",
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.Column("parent_id", sa.BigInteger(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name=op.f("fk_pages_owner_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["pages.id"],
            name=op.f("fk_pages_parent_id_pages"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pages")),
    )
    op.create_index(op.f("ix_pages_owner_id"), "pages", ["owner_id"], unique=False)
    op.create_index(op.f("ix_pages_parent_id"), "pages", ["parent_id"], unique=False)
    op.create_index(
        "ix_pages_owner_parent_position",
        "pages",
        ["owner_id", "parent_id", "position"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_pages_owner_parent_position", table_name="pages")
    op.drop_index(op.f("ix_pages_parent_id"), table_name="pages")
    op.drop_index(op.f("ix_pages_owner_id"), table_name="pages")
    op.drop_table("pages")
