import pytest

from md2blog.modules.workspace.application.service.pages import (
    CreatePage,
    DeletePage,
    GetPage,
    ListPages,
    MovePage,
    UpdatePage,
)
from md2blog.modules.workspace.domain.page import (
    InvalidPageMoveError,
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

    async def update(
        self,
        page: Page,
        *,
        title_changed: bool,
        content_changed: bool,
    ) -> Page:
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

    async def move(self, page: Page, parent_id: TSID | None, position: int) -> Page:
        remaining = [current for current in self.pages if current.id != page.id]
        siblings = sorted(
            (
                current
                for current in remaining
                if current.owner_id == page.owner_id and current.parent_id == parent_id
            ),
            key=lambda current: current.position,
        )
        target_position = min(position, len(siblings))
        moved = page.move_to(parent_id=parent_id, position=target_position)
        siblings.insert(target_position, moved)
        reordered = {
            sibling.id: sibling.move_to(parent_id=parent_id, position=index)
            for index, sibling in enumerate(siblings)
        }
        self.pages = [reordered.get(current.id, current) for current in remaining]
        self.pages.append(reordered[moved.id])
        return reordered[moved.id]

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


async def test_get_page_returns_owned_page_with_content() -> None:
    page = Page(id=TSID(2), owner_id=TSID(1), title="내 페이지", content="# 본문")

    result = await GetPage(InMemoryPages([page])).execute(page_id=page.id, owner_id=page.owner_id)

    assert result == page


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
        page_id=page.id,
        owner_id=owner_id,
        parent_id=parent.id,
        position=99,
    )

    assert moved.parent_id == parent.id
    assert moved.position == 1


async def test_move_page_reorders_pages_in_same_parent() -> None:
    owner_id = TSID(1)
    first = Page(id=TSID(2), owner_id=owner_id, title="첫 번째", content="", position=0)
    second = Page(id=TSID(3), owner_id=owner_id, title="두 번째", content="", position=1)
    pages = InMemoryPages([first, second])

    moved = await MovePage(pages).execute(
        page_id=second.id,
        owner_id=owner_id,
        parent_id=None,
        position=0,
    )

    assert moved.position == 0
    positions = {page.id: page.position for page in pages.pages}
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
            page_id=parent.id,
            owner_id=owner_id,
            parent_id=child.id,
            position=0,
        )


async def test_move_page_rejects_parent_owned_by_another_user() -> None:
    page = Page(id=TSID(2), owner_id=TSID(1), title="내 페이지", content="")
    other_parent = Page(id=TSID(3), owner_id=TSID(99), title="다른 사용자", content="")

    with pytest.raises(ParentPageNotFoundError):
        await MovePage(InMemoryPages([page, other_parent])).execute(
            page_id=page.id,
            owner_id=page.owner_id,
            parent_id=other_parent.id,
            position=0,
        )
