from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

from md2blog.modules.workspace.application.port.outbound.object_storage import StoredObject
from md2blog.modules.workspace.application.service.pages import CleanupOrphanPageFiles


class InMemoryObjectStorage:
    def __init__(self, objects: list[StoredObject]) -> None:
        self.objects = objects
        self.deleted: list[str] = []

    async def list(self, prefix: str) -> list[StoredObject]:
        return [stored for stored in self.objects if stored.key.startswith(prefix)]

    async def delete(self, key: str) -> None:
        self.deleted.append(key)


async def test_cleanup_deletes_only_old_unreferenced_page_files() -> None:
    now = datetime(2026, 10, 3, 12, tzinfo=UTC)
    pages = AsyncMock()
    pages.list_file_keys.return_value = {"users/1/pdf/referenced.pdf"}
    storage = InMemoryObjectStorage(
        [
            StoredObject("users/1/pdf/referenced.pdf", now - timedelta(days=2)),
            StoredObject("users/1/pdf/orphan.pdf", now - timedelta(days=2)),
            StoredObject("users/1/pdf/uploading.pdf", now - timedelta(hours=1)),
        ]
    )

    deleted_count = await CleanupOrphanPageFiles(pages, storage).execute(now=now)

    assert deleted_count == 1
    assert storage.deleted == ["users/1/pdf/orphan.pdf"]
