from typing import Protocol

from md2blog.modules.workspace.application.model.pages import PageDetail, PageListItem
from md2blog.shared.domain.tsid import TSID


class PageQueryRepository(Protocol):
    async def find_all_by_owner_id(self, owner_id: TSID) -> list[PageListItem]: ...

    async def find_detail_by_id(
        self,
        page_id: TSID,
        owner_id: TSID,
    ) -> PageDetail | None: ...
