from typing import Protocol

from md2blog.modules.workspace.application.model.pages import (
    PageDetail,
    PageListItem,
    TrashedPageListItem,
)
from md2blog.shared.domain.tsid import TSID


class PageQueryRepository(Protocol):
    async def find_all_by_owner_id(self, owner_id: TSID) -> list[PageListItem]: ...

    async def search_by_owner_id(
        self,
        owner_id: TSID,
        query: str,
    ) -> list[PageListItem]: ...

    async def find_detail_by_id(
        self,
        page_id: TSID,
        owner_id: TSID,
    ) -> PageDetail | None: ...

    async def find_all_trashed_by_owner_id(
        self,
        owner_id: TSID,
    ) -> list[TrashedPageListItem]: ...

    async def find_trashed_detail_by_id(
        self,
        page_id: TSID,
        owner_id: TSID,
    ) -> PageDetail | None: ...
