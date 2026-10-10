"""add memo page type

Revision ID: a8f3c1d72e46
Revises: c8d29a71f4b6
Create Date: 2026-10-10 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "a8f3c1d72e46"
down_revision: str | Sequence[str] | None = "c8d29a71f4b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_pages_page_type", "pages", type_="check")
    op.create_check_constraint(
        "ck_pages_page_type",
        "pages",
        "page_type IN ('MARKDOWN', 'HTML', 'MEMO', 'PDF')",
    )


def downgrade() -> None:
    op.execute("UPDATE pages SET page_type = 'MARKDOWN' WHERE page_type = 'MEMO'")
    op.drop_constraint("ck_pages_page_type", "pages", type_="check")
    op.create_check_constraint(
        "ck_pages_page_type",
        "pages",
        "page_type IN ('MARKDOWN', 'HTML', 'PDF')",
    )
