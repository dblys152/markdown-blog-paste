from dataclasses import dataclass
from datetime import datetime

from md2blog.modules.workspace.domain.page import Page
from md2blog.modules.workspace.domain.page_types import PageType
from md2blog.shared.domain.tsid import TSID


@dataclass(frozen=True, slots=True)
class PageListItem:
    id: TSID
    owner_id: TSID
    parent_id: TSID | None
    title: str
    sort_order: int
    page_type: PageType = PageType.MARKDOWN


@dataclass(frozen=True, slots=True)
class PageDetail:
    id: TSID
    owner_id: TSID
    parent_id: TSID | None
    title: str
    contents: str | None
    sort_order: int
    page_type: PageType = PageType.MARKDOWN
    file_name: str | None = None
    file_size: int | None = None

    @classmethod
    def from_domain(cls, page: Page) -> "PageDetail":
        return cls(
            id=page.id,
            owner_id=page.owner_id,
            parent_id=page.parent_id,
            title=page.title,
            contents=page.content.content if page.content is not None else None,
            sort_order=page.sort_order,
            page_type=page.page_type,
        )


@dataclass(frozen=True, slots=True)
class TrashedPageListItem:
    id: TSID
    parent_id: TSID | None
    title: str
    sort_order: int
    deleted_at: datetime
    expires_at: datetime
    page_type: PageType = PageType.MARKDOWN
