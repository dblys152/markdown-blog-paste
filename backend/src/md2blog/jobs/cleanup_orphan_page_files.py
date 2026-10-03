import asyncio

from md2blog.modules.workspace.application.service.pages import CleanupOrphanPageFiles
from md2blog.modules.workspace.infrastructure.object_storage import (
    get_configured_object_storage,
)
from md2blog.modules.workspace.infrastructure.repositories import SqlAlchemyPageRepository
from md2blog.shared.infrastructure.database import get_session_factory


async def cleanup_orphan_page_files() -> int:
    async with get_session_factory()() as session:
        return await CleanupOrphanPageFiles(
            SqlAlchemyPageRepository(session),
            get_configured_object_storage(),
        ).execute()


def main() -> None:
    count = asyncio.run(cleanup_orphan_page_files())
    print(f"Deleted {count} orphan page file(s).")


if __name__ == "__main__":
    main()
