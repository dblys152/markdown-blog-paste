from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta

from md2blog.modules.workspace.domain.commands import (
    CreatePageCommand,
    DeletePageCommand,
    MovePageCommand,
    RestorePageCommand,
    UpdatePageCommand,
)
from md2blog.shared.domain.tsid import TSID


@dataclass(frozen=True, slots=True)
class PageContent:
    page_id: TSID
    content: str

    def revise(self, content: str) -> "PageContent":
        return replace(self, content=content)


@dataclass(frozen=True, slots=True, kw_only=True)
class Page:
    id: TSID
    owner_id: TSID
    parent_id: TSID | None
    title: str
    content: PageContent
    sort_order: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    def __post_init__(self) -> None:
        normalized_title = self.title.strip()
        if not normalized_title:
            raise BlankPageTitleError
        if len(normalized_title) > 200:
            raise PageTitleTooLongError
        if self.sort_order < 0:
            raise InvalidPageSortOrderError
        if self.parent_id == self.id:
            raise InvalidPageParentError
        if self.content.page_id != self.id:
            raise InvalidPageContentError
        object.__setattr__(self, "title", normalized_title)

    @classmethod
    def create(
        cls,
        command: CreatePageCommand,
        *,
        created_at: datetime | None = None,
    ) -> "Page":
        page_id = TSID.generate()
        now = created_at or datetime.now(UTC)
        return cls(
            id=page_id,
            owner_id=command.owner_id,
            title=command.title,
            content=PageContent(page_id=page_id, content=command.content),
            parent_id=command.parent_id,
            sort_order=command.sort_order,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )

    def update(
        self,
        command: UpdatePageCommand,
        *,
        changed_at: datetime | None = None,
    ) -> "Page":
        if command.page_id != self.id or command.owner_id != self.owner_id:
            raise InvalidPageCommandTargetError
        page = self
        now = changed_at or datetime.now(UTC)
        if command.title is not None:
            page = replace(page, title=command.title, updated_at=now)
        if command.content is not None:
            page = replace(
                page,
                content=page.content.revise(command.content),
                updated_at=now,
            )
        return page

    def rename(self, title: str, *, changed_at: datetime | None = None) -> "Page":
        return replace(
            self,
            title=title,
            updated_at=changed_at or datetime.now(UTC),
        )

    def revise_content(
        self,
        content: str,
        *,
        changed_at: datetime | None = None,
    ) -> "Page":
        return replace(
            self,
            content=self.content.revise(content),
            updated_at=changed_at or datetime.now(UTC),
        )

    def move_to(
        self,
        command: MovePageCommand,
        *,
        changed_at: datetime | None = None,
    ) -> "Page":
        if command.page_id != self.id or command.owner_id != self.owner_id:
            raise InvalidPageCommandTargetError
        if command.parent_id == self.id:
            raise InvalidPageMoveError
        return replace(
            self,
            parent_id=command.parent_id,
            sort_order=command.sort_order,
            updated_at=changed_at or datetime.now(UTC),
        )

    def trash(
        self,
        command: DeletePageCommand,
        *,
        deleted_at: datetime | None = None,
    ) -> "Page":
        if command.page_id != self.id or command.owner_id != self.owner_id:
            raise InvalidPageCommandTargetError
        now = deleted_at or datetime.now(UTC)
        return replace(self, updated_at=now, deleted_at=now)

    def restore(
        self,
        command: RestorePageCommand,
        *,
        restored_at: datetime | None = None,
    ) -> "Page":
        if command.page_id != self.id or command.owner_id != self.owner_id:
            raise InvalidPageCommandTargetError
        return replace(
            self,
            updated_at=restored_at or datetime.now(UTC),
            deleted_at=None,
        )

    @property
    def is_trashed(self) -> bool:
        return self.deleted_at is not None

    def is_expired(self, now: datetime) -> bool:
        return self.deleted_at is not None and self.deleted_at + timedelta(days=30) <= now


class PageNotFoundError(Exception):
    pass


class PageDomainError(Exception):
    pass


class BlankPageTitleError(PageDomainError):
    pass


class PageTitleTooLongError(PageDomainError):
    pass


class InvalidPageSortOrderError(PageDomainError):
    pass


class InvalidPageParentError(PageDomainError):
    pass


class InvalidPageContentError(PageDomainError):
    pass


class InvalidPageMoveError(PageDomainError):
    pass


class InvalidPageCommandTargetError(PageDomainError):
    pass


class ParentPageNotFoundError(Exception):
    pass
