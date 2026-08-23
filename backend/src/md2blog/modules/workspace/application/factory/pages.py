from md2blog.modules.workspace.domain.commands import CreatePageCommand
from md2blog.modules.workspace.domain.page import ParentPageNotFoundError
from md2blog.modules.workspace.domain.repositories import PageRepository
from md2blog.shared.domain.tsid import TSID


class CreatePageCommandFactory:
    def __init__(self, pages: PageRepository) -> None:
        self._pages = pages

    async def create(
        self,
        *,
        owner_id: TSID,
        title: str,
        content: str,
        parent_id: TSID | None,
    ) -> CreatePageCommand:
        sort_order = await self._pages.next_sort_order(owner_id, parent_id)
        if sort_order is None:
            raise ParentPageNotFoundError

        return CreatePageCommand(
            owner_id=owner_id,
            title=title,
            content=content,
            parent_id=parent_id,
            sort_order=sort_order,
        )
