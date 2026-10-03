from datetime import datetime
from typing import Protocol

from md2blog.modules.workspace.domain.page import Page
from md2blog.shared.domain.tsid import TSID


class PageRepository(Protocol):
    async def add(self, page: Page) -> None: ...

    async def update(self, page: Page) -> None: ...

    async def update_all(self, pages: list[Page]) -> None: ...

    async def delete(self, page: Page) -> None: ...

    async def find_by_id(self, page_id: TSID, owner_id: TSID) -> Page | None: ...

    async def find_trashed_by_id(self, page_id: TSID, owner_id: TSID) -> Page | None: ...

    async def find_all_by_parent_id(
        self,
        owner_id: TSID,
        parent_id: TSID | None,
        *,
        exclude_id: TSID | None = None,
    ) -> list[Page]: ...

    async def find_all_trashed_by_parent_id(
        self,
        owner_id: TSID,
        parent_id: TSID,
    ) -> list[Page]: ...

    async def next_sort_order(
        self,
        owner_id: TSID,
        parent_id: TSID | None,
    ) -> int | None: ...

    async def delete_expired(self, threshold: datetime) -> int: ...

    async def add_file(
        self,
        *,
        page_id: TSID,
        storage_key: str,
        original_filename: str,
        media_type: str,
        byte_size: int,
        checksum_sha256: str,
    ) -> None: ...

    async def total_file_bytes(self, owner_id: TSID) -> int: ...

    async def find_file_key(self, page_id: TSID, owner_id: TSID) -> str | None: ...
