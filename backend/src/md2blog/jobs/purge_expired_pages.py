import asyncio

from md2blog.modules.workspace.application.service.pages import PurgeExpiredPages
from md2blog.modules.workspace.infrastructure.repositories import SqlAlchemyPageRepository
from md2blog.shared.infrastructure.database import get_session_factory


async def purge_expired_pages() -> int:
    async with get_session_factory()() as session:
        try:
            count = await PurgeExpiredPages(SqlAlchemyPageRepository(session)).execute()
            await session.commit()
            return count
        except Exception:
            await session.rollback()
            raise


def main() -> None:
    count = asyncio.run(purge_expired_pages())
    print(f"Purged {count} expired page(s).")


if __name__ == "__main__":
    main()
