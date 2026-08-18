from dataclasses import dataclass, replace
from datetime import datetime

from md2blog.shared.domain.tsid import TSID


@dataclass(frozen=True, slots=True)
class Page:
    id: TSID
    owner_id: TSID
    title: str
    content: str
    parent_id: TSID | None = None
    position: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        normalized_title = self.title.strip()
        if not normalized_title:
            raise ValueError("page title must not be blank")
        if len(normalized_title) > 200:
            raise ValueError("page title must not exceed 200 characters")
        if self.position < 0:
            raise ValueError("page position must not be negative")
        object.__setattr__(self, "title", normalized_title)

    @classmethod
    def create(
        cls,
        *,
        owner_id: TSID,
        title: str,
        content: str = "",
        parent_id: TSID | None = None,
        position: int = 0,
    ) -> "Page":
        return cls(
            id=TSID.generate(),
            owner_id=owner_id,
            title=title,
            content=content,
            parent_id=parent_id,
            position=position,
        )

    def revise(self, *, title: str | None = None, content: str | None = None) -> "Page":
        return replace(
            self,
            title=self.title if title is None else title,
            content=self.content if content is None else content,
        )

    def move_to(self, *, parent_id: TSID | None, position: int) -> "Page":
        if parent_id == self.id:
            raise InvalidPageMoveError
        return replace(self, parent_id=parent_id, position=position)


class PageNotFoundError(Exception):
    pass


class InvalidPageMoveError(Exception):
    pass


class ParentPageNotFoundError(Exception):
    pass
