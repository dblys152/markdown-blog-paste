from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from md2blog.modules.workspace.application.model.pages import (
    PageDetail,
    PageListItem,
    TrashedPageListItem,
)
from md2blog.modules.workspace.domain.page_types import PageType
from md2blog.shared.domain.tsid import TSID

MAX_TEXT_CONTENT_BYTES = 5 * 1024 * 1024


class CreatePageRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = ""
    parent_id: str | None = None
    type: PageType = PageType.MARKDOWN

    @model_validator(mode="after")
    def validate_page_type_and_size(self) -> "CreatePageRequest":
        if self.type is PageType.PDF:
            raise ValueError("PDF pages must be created through /workspace/pages/pdf")
        if len(self.content.encode("utf-8")) > MAX_TEXT_CONTENT_BYTES:
            raise ValueError("page content must not exceed 5 MB")
        return self

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
        if self.content is not None and len(self.content.encode("utf-8")) > MAX_TEXT_CONTENT_BYTES:
            raise ValueError("page content must not exceed 5 MB")
        return self


class MovePageRequest(BaseModel):
    parent_id: str | None
    sort_order: int = Field(ge=0)

    @field_validator("parent_id")
    @classmethod
    def validate_parent_id(cls, value: str | None) -> str | None:
        if value is not None:
            TSID.from_string(value)
        return value


class PageDetailResponse(BaseModel):
    id: str
    owner_id: str
    title: str
    contents: str | None
    parent_id: str | None
    sort_order: int
    type: PageType
    file_name: str | None = None
    file_size: int | None = None

    @classmethod
    def from_model(cls, page: PageDetail) -> "PageDetailResponse":
        return cls(
            id=str(page.id),
            owner_id=str(page.owner_id),
            title=page.title,
            contents=page.contents,
            parent_id=str(page.parent_id) if page.parent_id else None,
            sort_order=page.sort_order,
            type=page.page_type,
            file_name=page.file_name,
            file_size=page.file_size,
        )


class PageListItemResponse(BaseModel):
    id: str
    owner_id: str
    title: str
    parent_id: str | None
    sort_order: int
    type: PageType

    @classmethod
    def from_model(cls, page: PageListItem) -> "PageListItemResponse":
        return cls(
            id=str(page.id),
            owner_id=str(page.owner_id),
            title=page.title,
            parent_id=str(page.parent_id) if page.parent_id else None,
            sort_order=page.sort_order,
            type=page.page_type,
        )


class TrashedPageListItemResponse(BaseModel):
    id: str
    parent_id: str | None
    title: str
    sort_order: int
    deleted_at: datetime
    expires_at: datetime
    type: PageType

    @classmethod
    def from_model(cls, page: TrashedPageListItem) -> "TrashedPageListItemResponse":
        return cls(
            id=str(page.id),
            parent_id=str(page.parent_id) if page.parent_id else None,
            title=page.title,
            sort_order=page.sort_order,
            deleted_at=page.deleted_at,
            expires_at=page.expires_at,
            type=page.page_type,
        )
