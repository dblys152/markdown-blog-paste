from md2blog.modules.workspace.domain.page import Page, ParentPageNotFoundError
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

    async def execute(self, owner_id: TSID) -> list[Page]:
        return await self._pages.list_by_owner(owner_id)
