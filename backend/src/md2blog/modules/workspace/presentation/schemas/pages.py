from pydantic import BaseModel, Field, field_validator, model_validator

from md2blog.modules.workspace.application.model.pages import PageDetail, PageListItem
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
    contents: str
    parent_id: str | None
    sort_order: int

    @classmethod
    def from_model(cls, page: PageDetail) -> "PageDetailResponse":
        return cls(
            id=str(page.id),
            owner_id=str(page.owner_id),
            title=page.title,
            contents=page.contents,
            parent_id=str(page.parent_id) if page.parent_id else None,
            sort_order=page.sort_order,
        )


class PageListItemResponse(BaseModel):
    id: str
    owner_id: str
    title: str
    parent_id: str | None
    sort_order: int

    @classmethod
    def from_model(cls, page: PageListItem) -> "PageListItemResponse":
        return cls(
            id=str(page.id),
            owner_id=str(page.owner_id),
            title=page.title,
            parent_id=str(page.parent_id) if page.parent_id else None,
            sort_order=page.sort_order,
        )
