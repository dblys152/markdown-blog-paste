import pytest

from md2blog.modules.workspace.application.service.pages import (
    CreatePage,
    DeletePage,
    ListPages,
    UpdatePage,
)
from md2blog.modules.workspace.domain.page import (
    Page,
    PageNotFoundError,
    ParentPageNotFoundError,
)
from md2blog.shared.domain.tsid import TSID


class InMemoryPages:
    def __init__(self, pages: list[Page] | None = None) -> None:
        self.pages = pages or []

    async def add(self, page: Page) -> Page:
        self.pages.append(page)
        return page

    async def update(self, page: Page) -> Page:
        self.pages = [page if current.id == page.id else current for current in self.pages]
        return page

    async def delete(self, page: Page) -> None:
        deleted_ids = {page.id}
        while True:
            children = {current.id for current in self.pages if current.parent_id in deleted_ids}
            if children.issubset(deleted_ids):
                break
            deleted_ids.update(children)
        self.pages = [current for current in self.pages if current.id not in deleted_ids]

    async def find_owned_by_id(self, page_id: TSID, owner_id: TSID) -> Page | None:
        return next(
            (page for page in self.pages if page.id == page_id and page.owner_id == owner_id),
            None,
        )

    async def list_by_owner(self, owner_id: TSID) -> list[Page]:
        return [page for page in self.pages if page.owner_id == owner_id]

    async def next_position(self, owner_id: TSID, parent_id: TSID | None) -> int:
        siblings = [
            page for page in self.pages if page.owner_id == owner_id and page.parent_id == parent_id
        ]
        return max((page.position for page in siblings), default=-1) + 1


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

    created = await CreatePage(pages).execute(
        owner_id=owner_id,
        parent_id=parent.id,
        title=" API 설계 ",
        content="# API 설계",
    )

    assert created.title == "API 설계"
    assert created.parent_id == parent.id
    assert created.position == 1


async def test_create_page_rejects_parent_owned_by_another_user() -> None:
    parent = Page(id=TSID(2), owner_id=TSID(99), title="다른 사용자 페이지", content="")

    with pytest.raises(ParentPageNotFoundError):
        await CreatePage(InMemoryPages([parent])).execute(
            owner_id=TSID(1),
            parent_id=parent.id,
            title="하위 페이지",
            content="",
        )


async def test_list_pages_returns_only_owner_pages() -> None:
    mine = Page(id=TSID(2), owner_id=TSID(1), title="내 페이지", content="")
    other = Page(id=TSID(3), owner_id=TSID(99), title="다른 페이지", content="")

    result = await ListPages(InMemoryPages([mine, other])).execute(TSID(1))

    assert result == [mine]


async def test_update_page_revises_only_provided_fields() -> None:
    original = Page(
        id=TSID(2),
        owner_id=TSID(1),
        title="개발 노트",
        content="# 이전 본문",
    )
    pages = InMemoryPages([original])

    updated = await UpdatePage(pages).execute(
        page_id=original.id,
        owner_id=original.owner_id,
        title=None,
        content="# 변경된 본문",
    )

    assert updated.title == "개발 노트"
    assert updated.content == "# 변경된 본문"
    assert pages.pages == [updated]


async def test_update_page_hides_another_users_page_as_not_found() -> None:
    other = Page(id=TSID(2), owner_id=TSID(99), title="다른 페이지", content="")

    with pytest.raises(PageNotFoundError):
        await UpdatePage(InMemoryPages([other])).execute(
            page_id=other.id,
            owner_id=TSID(1),
            title="탈취 시도",
            content=None,
        )


async def test_delete_page_removes_page_and_descendants() -> None:
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

    await DeletePage(pages).execute(page_id=parent.id, owner_id=parent.owner_id)

    assert pages.pages == []


async def test_delete_page_hides_another_users_page_as_not_found() -> None:
    other = Page(id=TSID(2), owner_id=TSID(99), title="다른 페이지", content="")

    with pytest.raises(PageNotFoundError):
        await DeletePage(InMemoryPages([other])).execute(
            page_id=other.id,
            owner_id=TSID(1),
        )
