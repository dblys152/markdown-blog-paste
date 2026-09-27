import asyncio

from md2blog.modules.workspace.application.service.pages import PurgeExpiredPages
from md2blog.modules.workspace.infrastructure.repositories import SqlAlchemyPageRepository
from md2blog.shared.infrastructure.database import (
    SqlAlchemyUnitOfWork,
    get_session_factory,
)


async def purge_expired_pages() -> int:
    async with get_session_factory()() as session:
        return await PurgeExpiredPages(
            SqlAlchemyPageRepository(session),
            SqlAlchemyUnitOfWork(session),
        ).execute()


def main() -> None:
    count = asyncio.run(purge_expired_pages())
    print(f"Purged {count} expired page(s).")


if __name__ == "__main__":
    main()
