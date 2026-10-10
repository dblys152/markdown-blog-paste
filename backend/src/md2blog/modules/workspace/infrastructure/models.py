from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from md2blog.shared.infrastructure.persistence import Base, TimestampMixin, TSIDPrimaryKeyMixin


class PageModel(TSIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "pages"
    __table_args__ = (
        Index("ix_pages_owner_parent_sort_order", "owner_id", "parent_id", "sort_order"),
        CheckConstraint(
            "page_type IN ('MARKDOWN', 'HTML', 'MEMO', 'PDF')",
            name="ck_pages_page_type",
        ),
    )

    owner_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("pages.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    page_type: Mapped[str] = mapped_column(String(16), nullable=False, default="MARKDOWN")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    content_record: Mapped["PageContentModel"] = relationship(
        back_populates="page",
        cascade="all, delete-orphan",
        lazy="raise",
        single_parent=True,
        uselist=False,
    )


class PageContentModel(TimestampMixin, Base):
    __tablename__ = "page_contents"

    page_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("pages.id", ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    page: Mapped[PageModel] = relationship(back_populates="content_record", lazy="raise")


class PageFileModel(TimestampMixin, Base):
    __tablename__ = "page_files"
    __table_args__ = (CheckConstraint("byte_size > 0", name="ck_page_files_byte_size"),)

    page_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("pages.id", ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
    )
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    media_type: Mapped[str] = mapped_column(String(100), nullable=False)
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
