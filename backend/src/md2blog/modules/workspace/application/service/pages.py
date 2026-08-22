from md2blog.modules.workspace.application.model.pages import PageDetail, PageListItem
from md2blog.modules.workspace.application.port.outbound.pages import PageQueryRepository
from md2blog.modules.workspace.domain.commands import (
    CreatePageCommand,
    DeletePageCommand,
    MovePageCommand,
    UpdatePageCommand,
)
from md2blog.modules.workspace.domain.page import (
    InvalidPageMoveError,
    Page,
    PageNotFoundError,
    ParentPageNotFoundError,
)
from md2blog.modules.workspace.domain.repositories import PageRepository
from md2blog.shared.domain.tsid import TSID


class CreatePage:
    def __init__(self, pages: PageRepository) -> None:
        self._pages = pages

    async def execute(self, command: CreatePageCommand) -> PageDetail:
        page = Page.create(command)
        await self._pages.add(page)
        return PageDetail.from_domain(page)


class ListPages:
    def __init__(self, page_queries: PageQueryRepository) -> None:
        self._page_queries = page_queries

    async def execute(self, owner_id: TSID) -> list[PageListItem]:
        return await self._page_queries.find_all_by_owner_id(owner_id)


class GetPage:
    def __init__(self, page_queries: PageQueryRepository) -> None:
        self._page_queries = page_queries

    async def execute(self, *, page_id: TSID, owner_id: TSID) -> PageDetail:
        page = await self._page_queries.find_detail_by_id(page_id, owner_id)
        if page is None:
            raise PageNotFoundError
        return page


class UpdatePage:
    def __init__(self, pages: PageRepository) -> None:
        self._pages = pages

    async def execute(self, command: UpdatePageCommand) -> PageDetail:
        page = await self._pages.find_by_id(command.page_id, command.owner_id)
        if page is None:
            raise PageNotFoundError
        page = page.update(command)
        await self._pages.update(page)
        return PageDetail.from_domain(page)


class DeletePage:
    def __init__(self, pages: PageRepository) -> None:
        self._pages = pages

    async def execute(self, command: DeletePageCommand) -> None:
        page = await self._pages.find_by_id(command.page_id, command.owner_id)
        if page is None:
            raise PageNotFoundError
        await self._pages.delete(page)


class MovePage:
    def __init__(self, pages: PageRepository) -> None:
        self._pages = pages

    async def execute(self, command: MovePageCommand) -> PageDetail:
        page = await self._pages.find_by_id(command.page_id, command.owner_id)
        if page is None:
            raise PageNotFoundError

        await self._ensure_valid_parent(page, command.parent_id)
        old_parent_id = page.parent_id
        old_siblings = await self._pages.find_all_by_parent_id(
            command.owner_id,
            old_parent_id,
            exclude_id=page.id,
        )
        target_siblings = (
            old_siblings
            if old_parent_id == command.parent_id
            else await self._pages.find_all_by_parent_id(
                command.owner_id,
                command.parent_id,
                exclude_id=page.id,
            )
        )
        target_position = min(command.sort_order, len(target_siblings))
        target_siblings.insert(target_position, page)
        moved_target = [
            sibling.move_to(
                MovePageCommand(
                    page_id=sibling.id,
                    owner_id=sibling.owner_id,
                    parent_id=command.parent_id,
                    sort_order=index,
                )
            )
            for index, sibling in enumerate(target_siblings)
        ]
        changed_pages = moved_target
        if old_parent_id != command.parent_id:
            changed_pages = [
                *[
                    sibling.move_to(
                        MovePageCommand(
                            page_id=sibling.id,
                            owner_id=sibling.owner_id,
                            parent_id=old_parent_id,
                            sort_order=index,
                        )
                    )
                    for index, sibling in enumerate(old_siblings)
                ],
                *moved_target,
            ]
        await self._pages.update_all(changed_pages)
        moved_page = moved_target[target_position]
        return PageDetail.from_domain(moved_page)

    async def _ensure_valid_parent(self, page: Page, parent_id: TSID | None) -> None:
        current_id = parent_id
        visited: set[TSID] = set()
        while current_id is not None:
            if current_id == page.id or current_id in visited:
                raise InvalidPageMoveError
            visited.add(current_id)
            current = await self._pages.find_by_id(current_id, page.owner_id)
            if current is None:
                raise ParentPageNotFoundError
            current_id = current.parent_id
