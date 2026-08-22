from dataclasses import dataclass

from md2blog.modules.workspace.domain.page import Page
from md2blog.shared.domain.tsid import TSID


@dataclass(frozen=True, slots=True)
class PageListItem:
    id: TSID
    owner_id: TSID
    parent_id: TSID | None
    title: str
    sort_order: int


@dataclass(frozen=True, slots=True)
class PageDetail:
    id: TSID
    owner_id: TSID
    parent_id: TSID | None
    title: str
    contents: str
    sort_order: int

    @classmethod
    def from_domain(cls, page: Page) -> "PageDetail":
        return cls(
            id=page.id,
            owner_id=page.owner_id,
            parent_id=page.parent_id,
            title=page.title,
            contents=page.content.content,
            sort_order=page.sort_order,
        )
