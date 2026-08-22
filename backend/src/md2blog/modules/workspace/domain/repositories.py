from typing import Protocol

from md2blog.modules.workspace.domain.page import Page
from md2blog.shared.domain.tsid import TSID


class PageRepository(Protocol):
    async def add(self, page: Page) -> None: ...

    async def update(self, page: Page) -> None: ...

    async def update_all(self, pages: list[Page]) -> None: ...

    async def delete(self, page: Page) -> None: ...

    async def find_by_id(self, page_id: TSID, owner_id: TSID) -> Page | None: ...

    async def find_all_by_parent_id(
        self,
        owner_id: TSID,
        parent_id: TSID | None,
        *,
        exclude_id: TSID | None = None,
    ) -> list[Page]: ...

    async def next_sort_order(self, owner_id: TSID, parent_id: TSID | None) -> int: ...
