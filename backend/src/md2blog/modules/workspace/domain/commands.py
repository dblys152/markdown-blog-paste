from dataclasses import dataclass

from md2blog.shared.domain.tsid import TSID


@dataclass(frozen=True, slots=True)
class CreatePageCommand:
    owner_id: TSID
    title: str
    content: str
    parent_id: TSID | None
    sort_order: int


@dataclass(frozen=True, slots=True)
class UpdatePageCommand:
    page_id: TSID
    owner_id: TSID
    title: str | None
    content: str | None


@dataclass(frozen=True, slots=True)
class DeletePageCommand:
    page_id: TSID
    owner_id: TSID


@dataclass(frozen=True, slots=True)
class MovePageCommand:
    page_id: TSID
    owner_id: TSID
    parent_id: TSID | None
    sort_order: int
