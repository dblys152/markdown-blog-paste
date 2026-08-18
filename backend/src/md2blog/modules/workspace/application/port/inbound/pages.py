from typing import Protocol

from pydantic import BaseModel, Field, field_validator

from md2blog.modules.workspace.domain.page import Page
from md2blog.shared.domain.tsid import TSID


class CreatePageRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = ""
    parent_id: str | None = None

    @field_validator("parent_id")
    @classmethod
    def validate_parent_id(cls, value: str | None) -> str | None:
        if value is not None:
            TSID.from_string(value)
        return value


class PageResponse(BaseModel):
    id: str
    title: str
    content: str
    parent_id: str | None
    position: int

    @classmethod
    def from_domain(cls, page: Page) -> "PageResponse":
        return cls(
            id=str(page.id),
            title=page.title,
            content=page.content,
            parent_id=str(page.parent_id) if page.parent_id else None,
            position=page.position,
        )


class CreatePageUseCase(Protocol):
    async def execute(
        self,
        *,
        owner_id: TSID,
        title: str,
        content: str,
        parent_id: TSID | None,
    ) -> Page: ...


class ListPagesUseCase(Protocol):
    async def execute(self, owner_id: TSID) -> list[Page]: ...
