from typing import Protocol

from md2blog.modules.workspace.domain.page import Page, PageListItem
from md2blog.shared.domain.tsid import TSID


class PageRepository(Protocol):
    async def add(self, page: Page) -> Page: ...

    async def update(
        self,
        page: Page,
        *,
        title_changed: bool,
        content_changed: bool,
    ) -> Page: ...

    async def delete(self, page: Page) -> None: ...

    async def move(self, page: Page, parent_id: TSID | None, position: int) -> Page: ...

    async def find_owned_by_id(self, page_id: TSID, owner_id: TSID) -> Page | None: ...

    async def list_by_owner(self, owner_id: TSID) -> list[PageListItem]: ...

    async def next_position(self, owner_id: TSID, parent_id: TSID | None) -> int: ...
