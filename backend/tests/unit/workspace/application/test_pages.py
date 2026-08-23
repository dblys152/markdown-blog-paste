from datetime import UTC, datetime, timedelta

import pytest

from md2blog.modules.workspace.application.factory.pages import CreatePageCommandFactory
from md2blog.modules.workspace.application.model.pages import (
    PageDetail,
    PageListItem,
    TrashedPageListItem,
)
from md2blog.modules.workspace.application.service.pages import (
    CreatePage,
    DeletePage,
    GetPage,
    ListPages,
    ListTrashedPages,
    MovePage,
    PermanentlyDeletePage,
    PurgeExpiredPages,
    RestorePage,
    SearchPages,
    UpdatePage,
)
from md2blog.modules.workspace.domain.commands import (
    DeletePageCommand,
    MovePageCommand,
    PermanentlyDeletePageCommand,
    RestorePageCommand,
    UpdatePageCommand,
)
from md2blog.modules.workspace.domain.page import (
    InvalidPageMoveError,
    PageContent,
    PageNotFoundError,
    ParentPageNotFoundError,
)
from md2blog.modules.workspace.domain.page import Page as DomainPage
from md2blog.shared.domain.tsid import TSID


class Page(DomainPage):
    def __init__(
        self,
        *,
        id: TSID,
        owner_id: TSID,
        title: str,
        content: str | PageContent,
        parent_id: TSID | None = None,
        sort_order: int = 0,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        deleted_at: datetime | None = None,
    ) -> None:
        super().__init__(
            id=id,
            owner_id=owner_id,
            title=title,
            content=(
                content
                if isinstance(content, PageContent)
                else PageContent(page_id=id, content=content)
            ),
            parent_id=parent_id,
            sort_order=sort_order,
            created_at=created_at or datetime(2026, 1, 1, tzinfo=UTC),
            updated_at=updated_at or datetime(2026, 1, 1, tzinfo=UTC),
            deleted_at=deleted_at,
        )


class InMemoryPages:
    def __init__(self, pages: list[Page] | None = None) -> None:
        self.pages = pages or []

    async def add(self, page: Page) -> None:
        self.pages.append(page)

    async def update(self, page: Page) -> None:
        self.pages = [page if current.id == page.id else current for current in self.pages]

    async def update_all(self, pages: list[Page]) -> None:
        updated = {page.id: page for page in pages}
        self.pages = [updated.get(current.id, current) for current in self.pages]

    async def delete(self, page: Page) -> None:
        deleted_ids = {page.id}
        while True:
            children = {current.id for current in self.pages if current.parent_id in deleted_ids}
            if children.issubset(deleted_ids):
                break
            deleted_ids.update(children)
        self.pages = [current for current in self.pages if current.id not in deleted_ids]

    async def find_by_id(self, page_id: TSID, owner_id: TSID) -> Page | None:
        return next(
            (
                page
                for page in self.pages
                if page.id == page_id
                and page.owner_id == owner_id
                and not page.is_trashed
            ),
            None,
        )

    async def find_trashed_by_id(self, page_id: TSID, owner_id: TSID) -> Page | None:
        return next(
            (
                page
                for page in self.pages
                if page.id == page_id and page.owner_id == owner_id and page.is_trashed
            ),
            None,
        )

    async def find_all_by_parent_id(
        self,
        owner_id: TSID,
        parent_id: TSID | None,
        *,
        exclude_id: TSID | None = None,
    ) -> list[Page]:
        return sorted(
            (
                page
                for page in self.pages
                if page.owner_id == owner_id
                and page.parent_id == parent_id
                and page.id != exclude_id
                and not page.is_trashed
            ),
            key=lambda page: page.sort_order,
        )

    async def find_all_trashed_by_parent_id(
        self,
        owner_id: TSID,
        parent_id: TSID,
    ) -> list[Page]:
        return [
            page
            for page in self.pages
            if page.owner_id == owner_id and page.parent_id == parent_id and page.is_trashed
        ]

    async def find_all_by_owner_id(self, owner_id: TSID) -> list[PageListItem]:
        return [
            PageListItem(
                id=page.id,
                owner_id=page.owner_id,
                parent_id=page.parent_id,
                title=page.title,
                sort_order=page.sort_order,
            )
            for page in self.pages
            if page.owner_id == owner_id
            and not page.is_trashed
        ]

    async def search_by_owner_id(self, owner_id: TSID, query: str) -> list[PageListItem]:
        normalized_query = query.casefold()
        return [
            PageListItem(
                id=page.id,
                owner_id=page.owner_id,
                parent_id=page.parent_id,
                title=page.title,
                sort_order=page.sort_order,
            )
            for page in self.pages
            if page.owner_id == owner_id
            and not page.is_trashed
            and (
                normalized_query in page.title.casefold()
                or normalized_query in page.content.content.casefold()
            )
        ]

    async def find_detail_by_id(self, page_id: TSID, owner_id: TSID) -> PageDetail | None:
        page = await self.find_by_id(page_id, owner_id)
        return None if page is None else PageDetail.from_domain(page)

    async def find_all_trashed_by_owner_id(
        self,
        owner_id: TSID,
    ) -> list[TrashedPageListItem]:
        return [
            TrashedPageListItem(
                id=page.id,
                parent_id=page.parent_id,
                title=page.title,
                sort_order=page.sort_order,
                deleted_at=page.deleted_at,
                expires_at=page.deleted_at + timedelta(days=30),
            )
            for page in self.pages
            if page.owner_id == owner_id and page.deleted_at is not None
        ]

    async def find_trashed_detail_by_id(
        self,
        page_id: TSID,
        owner_id: TSID,
    ) -> PageDetail | None:
        page = await self.find_trashed_by_id(page_id, owner_id)
        return None if page is None else PageDetail.from_domain(page)

    async def next_sort_order(
        self,
        owner_id: TSID,
        parent_id: TSID | None,
    ) -> int | None:
        if parent_id is not None and not any(
            page.id == parent_id
            and page.owner_id == owner_id
            and not page.is_trashed
            for page in self.pages
        ):
            return None
        siblings = [
            page
            for page in self.pages
            if page.owner_id == owner_id
            and page.parent_id == parent_id
            and not page.is_trashed
        ]
        return max((page.sort_order for page in siblings), default=-1) + 1

    async def delete_expired(self, threshold: datetime) -> int:
        expired = [
            page for page in self.pages if page.deleted_at and page.deleted_at <= threshold
        ]
        self.pages = [page for page in self.pages if page not in expired]
        return len(expired)


async def test_create_page_appends_after_siblings() -> None:
    owner_id = TSID(1)
    parent = Page(id=TSID(2), owner_id=owner_id, title="개발 노트", content="")
    first_child = Page(
        id=TSID(3),
        owner_id=owner_id,
        parent_id=parent.id,
        title="인증",
        content="",
    )
    pages = InMemoryPages([parent, first_child])

    command = await CreatePageCommandFactory(pages).create(
        owner_id=owner_id,
        parent_id=parent.id,
        title=" API 설계 ",
        content="# API 설계",
    )
    created = await CreatePage(pages).execute(command)

    assert created.title == "API 설계"
    assert created.parent_id == parent.id
    assert created.sort_order == 1


async def test_create_page_rejects_parent_owned_by_another_user() -> None:
    parent = Page(id=TSID(2), owner_id=TSID(99), title="다른 사용자 페이지", content="")

    with pytest.raises(ParentPageNotFoundError):
        await CreatePageCommandFactory(InMemoryPages([parent])).create(
            owner_id=TSID(1),
            parent_id=parent.id,
            title="하위 페이지",
            content="",
        )


async def test_list_pages_returns_only_owner_pages() -> None:
    mine = Page(id=TSID(2), owner_id=TSID(1), title="내 페이지", content="")
    other = Page(id=TSID(3), owner_id=TSID(99), title="다른 페이지", content="")

    result = await ListPages(InMemoryPages([mine, other])).execute(TSID(1))

    assert [item.id for item in result] == [mine.id]


async def test_get_page_returns_owned_page_with_content() -> None:
    page = Page(id=TSID(2), owner_id=TSID(1), title="내 페이지", content="# 본문")

    result = await GetPage(InMemoryPages([page])).execute(page_id=page.id, owner_id=page.owner_id)

    assert result == PageDetail.from_domain(page)


async def test_update_page_revises_only_provided_fields() -> None:
    original = Page(
        id=TSID(2),
        owner_id=TSID(1),
        title="개발 노트",
        content="# 이전 본문",
    )
    pages = InMemoryPages([original])

    updated = await UpdatePage(pages).execute(
        UpdatePageCommand(
            page_id=original.id,
            owner_id=original.owner_id,
            title=None,
            content="# 변경된 본문",
        )
    )

    assert updated.title == "개발 노트"
    assert updated.contents == "# 변경된 본문"


async def test_update_page_hides_another_users_page_as_not_found() -> None:
    other = Page(id=TSID(2), owner_id=TSID(99), title="다른 페이지", content="")

    with pytest.raises(PageNotFoundError):
        await UpdatePage(InMemoryPages([other])).execute(
            UpdatePageCommand(
                page_id=other.id,
                owner_id=TSID(1),
                title="탈취 시도",
                content=None,
            )
        )


async def test_delete_page_moves_page_and_descendants_to_trash() -> None:
    parent = Page(id=TSID(2), owner_id=TSID(1), title="상위 페이지", content="")
    child = Page(
        id=TSID(3),
        owner_id=TSID(1),
        parent_id=parent.id,
        title="하위 페이지",
        content="",
    )
    grandchild = Page(
        id=TSID(4),
        owner_id=TSID(1),
        parent_id=child.id,
        title="손자 페이지",
        content="",
    )
    pages = InMemoryPages([parent, child, grandchild])

    await DeletePage(pages).execute(
        DeletePageCommand(page_id=parent.id, owner_id=parent.owner_id)
    )

    assert all(page.is_trashed for page in pages.pages)


async def test_delete_page_hides_another_users_page_as_not_found() -> None:
    other = Page(id=TSID(2), owner_id=TSID(99), title="다른 페이지", content="")

    with pytest.raises(PageNotFoundError):
        await DeletePage(InMemoryPages([other])).execute(
            DeletePageCommand(page_id=other.id, owner_id=TSID(1))
        )


async def test_restore_page_restores_page_and_descendants() -> None:
    deleted_at = datetime(2026, 1, 1, tzinfo=UTC)
    parent = Page(
        id=TSID(2), owner_id=TSID(1), title="상위", content="", deleted_at=deleted_at
    )
    child = Page(
        id=TSID(3),
        owner_id=TSID(1),
        parent_id=parent.id,
        title="하위",
        content="",
        deleted_at=deleted_at,
    )
    pages = InMemoryPages([parent, child])

    await RestorePage(pages).execute(
        RestorePageCommand(page_id=parent.id, owner_id=parent.owner_id)
    )

    assert all(not page.is_trashed for page in pages.pages)


async def test_list_trashed_pages_returns_deleted_pages() -> None:
    deleted_at = datetime(2026, 1, 1, tzinfo=UTC)
    page = Page(
        id=TSID(2), owner_id=TSID(1), title="휴지통", content="", deleted_at=deleted_at
    )

    result = await ListTrashedPages(InMemoryPages([page])).execute(page.owner_id)

    assert [item.id for item in result] == [page.id]
    assert result[0].expires_at == deleted_at + timedelta(days=30)


async def test_search_pages_finds_title_and_content_and_excludes_trash() -> None:
    owner_id = TSID(1)
    deleted_at = datetime(2026, 1, 1, tzinfo=UTC)
    pages = InMemoryPages(
        [
            Page(id=TSID(2), owner_id=owner_id, title="PostgreSQL", content=""),
            Page(id=TSID(3), owner_id=owner_id, title="성능 기록", content="VACUUM 점검"),
            Page(
                id=TSID(4),
                owner_id=owner_id,
                title="삭제됨",
                content="VACUUM",
                deleted_at=deleted_at,
            ),
            Page(id=TSID(5), owner_id=TSID(99), title="다른 사용자", content="VACUUM"),
        ]
    )

    title_result = await SearchPages(pages).execute(owner_id=owner_id, query="postgres")
    content_result = await SearchPages(pages).execute(owner_id=owner_id, query=" vacuum ")

    assert [page.id for page in title_result] == [TSID(2)]
    assert [page.id for page in content_result] == [TSID(3)]


async def test_permanently_delete_page_removes_trashed_tree() -> None:
    deleted_at = datetime(2026, 1, 1, tzinfo=UTC)
    page = Page(
        id=TSID(2), owner_id=TSID(1), title="삭제", content="", deleted_at=deleted_at
    )
    pages = InMemoryPages([page])

    await PermanentlyDeletePage(pages).execute(
        PermanentlyDeletePageCommand(page_id=page.id, owner_id=page.owner_id)
    )

    assert pages.pages == []


async def test_purge_expired_pages_hard_deletes_pages_after_30_days() -> None:
    now = datetime(2026, 2, 1, tzinfo=UTC)
    expired = Page(
        id=TSID(2),
        owner_id=TSID(1),
        title="만료",
        content="",
        deleted_at=now - timedelta(days=30),
    )
    retained = Page(
        id=TSID(3),
        owner_id=TSID(1),
        title="보관",
        content="",
        deleted_at=now - timedelta(days=29),
    )
    pages = InMemoryPages([expired, retained])

    count = await PurgeExpiredPages(pages).execute(now=now)

    assert count == 1
    assert pages.pages == [retained]


async def test_move_page_changes_parent_and_clamps_sibling_position() -> None:
    owner_id = TSID(1)
    page = Page(id=TSID(2), owner_id=owner_id, title="이동할 페이지", content="")
    parent = Page(id=TSID(3), owner_id=owner_id, title="상위 페이지", content="")
    child = Page(
        id=TSID(4),
        owner_id=owner_id,
        parent_id=parent.id,
        title="기존 하위 페이지",
        content="",
    )
    pages = InMemoryPages([page, parent, child])

    moved = await MovePage(pages).execute(
        MovePageCommand(
            page_id=page.id,
            owner_id=owner_id,
            parent_id=parent.id,
            sort_order=99,
        )
    )

    assert moved.parent_id == parent.id
    assert moved.sort_order == 1


async def test_move_page_reorders_pages_in_same_parent() -> None:
    owner_id = TSID(1)
    first = Page(id=TSID(2), owner_id=owner_id, title="첫 번째", content="", sort_order=0)
    second = Page(id=TSID(3), owner_id=owner_id, title="두 번째", content="", sort_order=1)
    pages = InMemoryPages([first, second])

    moved = await MovePage(pages).execute(
        MovePageCommand(
            page_id=second.id,
            owner_id=owner_id,
            parent_id=None,
            sort_order=0,
        )
    )

    assert moved.sort_order == 0
    positions = {page.id: page.sort_order for page in pages.pages}
    assert positions == {first.id: 1, second.id: 0}


async def test_move_page_rejects_descendant_as_parent() -> None:
    owner_id = TSID(1)
    parent = Page(id=TSID(2), owner_id=owner_id, title="상위", content="")
    child = Page(
        id=TSID(3),
        owner_id=owner_id,
        parent_id=parent.id,
        title="하위",
        content="",
    )

    with pytest.raises(InvalidPageMoveError):
        await MovePage(InMemoryPages([parent, child])).execute(
            MovePageCommand(
                page_id=parent.id,
                owner_id=owner_id,
                parent_id=child.id,
                sort_order=0,
            )
        )


async def test_move_page_rejects_parent_owned_by_another_user() -> None:
    page = Page(id=TSID(2), owner_id=TSID(1), title="내 페이지", content="")
    other_parent = Page(id=TSID(3), owner_id=TSID(99), title="다른 사용자", content="")

    with pytest.raises(ParentPageNotFoundError):
        await MovePage(InMemoryPages([page, other_parent])).execute(
            MovePageCommand(
                page_id=page.id,
                owner_id=page.owner_id,
                parent_id=other_parent.id,
                sort_order=0,
            )
        )
