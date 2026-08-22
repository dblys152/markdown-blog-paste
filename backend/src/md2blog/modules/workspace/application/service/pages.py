from md2blog.modules.workspace.domain.page import (
    InvalidPageMoveError,
    Page,
    PageListItem,
    PageNotFoundError,
    ParentPageNotFoundError,
)
from md2blog.modules.workspace.domain.repositories import PageRepository
from md2blog.shared.domain.tsid import TSID


class CreatePage:
    def __init__(self, pages: PageRepository) -> None:
        self._pages = pages

    async def execute(
        self,
        *,
        owner_id: TSID,
        title: str,
        content: str,
        parent_id: TSID | None,
    ) -> Page:
        if parent_id is not None:
            parent = await self._pages.find_owned_by_id(parent_id, owner_id)
            if parent is None:
                raise ParentPageNotFoundError

        position = await self._pages.next_position(owner_id, parent_id)
        return await self._pages.add(
            Page.create(
                owner_id=owner_id,
                title=title,
                content=content,
                parent_id=parent_id,
                position=position,
            )
        )


class ListPages:
    def __init__(self, pages: PageRepository) -> None:
        self._pages = pages

    async def execute(self, owner_id: TSID) -> list[PageListItem]:
        return await self._pages.list_by_owner(owner_id)


class GetPage:
    def __init__(self, pages: PageRepository) -> None:
        self._pages = pages

    async def execute(self, *, page_id: TSID, owner_id: TSID) -> Page:
        page = await self._pages.find_owned_by_id(page_id, owner_id)
        if page is None:
            raise PageNotFoundError
        return page


class UpdatePage:
    def __init__(self, pages: PageRepository) -> None:
        self._pages = pages

    async def execute(
        self,
        *,
        page_id: TSID,
        owner_id: TSID,
        title: str | None,
        content: str | None,
    ) -> Page:
        page = await self._pages.find_owned_by_id(page_id, owner_id)
        if page is None:
            raise PageNotFoundError
        return await self._pages.update(
            page.revise(title=title, content=content),
            title_changed=title is not None,
            content_changed=content is not None,
        )


class DeletePage:
    def __init__(self, pages: PageRepository) -> None:
        self._pages = pages

    async def execute(self, *, page_id: TSID, owner_id: TSID) -> None:
        page = await self._pages.find_owned_by_id(page_id, owner_id)
        if page is None:
            raise PageNotFoundError
        await self._pages.delete(page)


class MovePage:
    def __init__(self, pages: PageRepository) -> None:
        self._pages = pages

    async def execute(
        self,
        *,
        page_id: TSID,
        owner_id: TSID,
        parent_id: TSID | None,
        position: int,
    ) -> Page:
        page = await self._pages.find_owned_by_id(page_id, owner_id)
        if page is None:
            raise PageNotFoundError

        await self._ensure_valid_parent(page, parent_id)
        return await self._pages.move(page, parent_id, position)

    async def _ensure_valid_parent(self, page: Page, parent_id: TSID | None) -> None:
        current_id = parent_id
        visited: set[TSID] = set()
        while current_id is not None:
            if current_id == page.id or current_id in visited:
                raise InvalidPageMoveError
            visited.add(current_id)
            current = await self._pages.find_owned_by_id(current_id, page.owner_id)
            if current is None:
                raise ParentPageNotFoundError
            current_id = current.parent_id
