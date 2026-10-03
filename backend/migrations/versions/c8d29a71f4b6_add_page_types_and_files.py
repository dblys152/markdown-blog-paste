"""add page types and files

Revision ID: c8d29a71f4b6
Revises: f1a6c9d84e27
Create Date: 2026-10-03 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c8d29a71f4b6"
down_revision: str | Sequence[str] | None = "f1a6c9d84e27"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("pages", sa.Column("page_type", sa.String(length=16), nullable=True))
    op.execute("UPDATE pages SET page_type = 'MARKDOWN' WHERE page_type IS NULL")
    op.alter_column("pages", "page_type", nullable=False)
    op.create_check_constraint(
        "ck_pages_page_type", "pages", "page_type IN ('MARKDOWN', 'HTML', 'PDF')"
    )
    op.create_table(
        "page_files",
        sa.Column("page_id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("media_type", sa.String(length=100), nullable=False),
        sa.Column("byte_size", sa.BigInteger(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
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
        sa.CheckConstraint("byte_size > 0", name="ck_page_files_byte_size"),
        sa.ForeignKeyConstraint(["page_id"], ["pages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("page_id"),
        sa.UniqueConstraint("storage_key"),
    )


def downgrade() -> None:
    op.drop_table("page_files")
    op.drop_constraint("ck_pages_page_type", "pages", type_="check")
    op.drop_column("pages", "page_type")
