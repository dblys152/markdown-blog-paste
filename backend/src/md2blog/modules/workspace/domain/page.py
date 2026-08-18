from dataclasses import dataclass
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


class ParentPageNotFoundError(Exception):
    pass
