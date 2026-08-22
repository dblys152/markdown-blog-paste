from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from md2blog.shared.infrastructure.persistence import Base, TimestampMixin, TSIDPrimaryKeyMixin


class PageModel(TSIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "pages"
    __table_args__ = (Index("ix_pages_owner_parent_position", "owner_id", "parent_id", "position"),)

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
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class PageContentModel(TimestampMixin, Base):
    __tablename__ = "page_contents"

    page_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("pages.id", ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
