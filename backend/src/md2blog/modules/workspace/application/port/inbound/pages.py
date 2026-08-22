from typing import Protocol

from pydantic import BaseModel, Field, field_validator, model_validator

from md2blog.modules.workspace.domain.page import Page, PageListItem
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


class UpdatePageRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = None

    @model_validator(mode="after")
    def require_changes(self) -> "UpdatePageRequest":
        if self.title is None and self.content is None:
            raise ValueError("at least one page field must be provided")
        return self


class MovePageRequest(BaseModel):
    parent_id: str | None
    position: int = Field(ge=0)

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


class PageListItemResponse(BaseModel):
    id: str
    title: str
    parent_id: str | None
    position: int

    @classmethod
    def from_domain(cls, page: PageListItem) -> "PageListItemResponse":
        return cls(
            id=str(page.id),
            title=page.title,
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
    async def execute(self, owner_id: TSID) -> list[PageListItem]: ...


class GetPageUseCase(Protocol):
    async def execute(self, *, page_id: TSID, owner_id: TSID) -> Page: ...


class UpdatePageUseCase(Protocol):
    async def execute(
        self,
        *,
        page_id: TSID,
        owner_id: TSID,
        title: str | None,
        content: str | None,
    ) -> Page: ...


class DeletePageUseCase(Protocol):
    async def execute(self, *, page_id: TSID, owner_id: TSID) -> None: ...


class MovePageUseCase(Protocol):
    async def execute(
        self,
        *,
        page_id: TSID,
        owner_id: TSID,
        parent_id: TSID | None,
        position: int,
    ) -> Page: ...
