"""split page contents

Revision ID: 4b8c2f90e1a7
Revises: 98e05f91d164
Create Date: 2026-08-20 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "4b8c2f90e1a7"
down_revision: str | Sequence[str] | None = "98e05f91d164"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "page_contents",
        sa.Column("page_id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
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
            ["page_id"],
            ["pages.id"],
            name=op.f("fk_page_contents_page_id_pages"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("page_id", name=op.f("pk_page_contents")),
    )
    op.execute(
        """
        INSERT INTO page_contents (page_id, content, created_at, updated_at)
        SELECT id, content, created_at, updated_at
        FROM pages
        """
    )
    op.drop_column("pages", "content")


def downgrade() -> None:
    op.add_column(
        "pages",
        sa.Column("content", sa.Text(), server_default="", nullable=False),
    )
    op.execute(
        """
        UPDATE pages
        SET content = page_contents.content
        FROM page_contents
        WHERE pages.id = page_contents.page_id
        """
    )
    op.alter_column("pages", "content", server_default=None)
    op.drop_table("page_contents")
