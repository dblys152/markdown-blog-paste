from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from md2blog.modules.workspace.domain.page import Page
from md2blog.modules.workspace.infrastructure.models import PageModel
from md2blog.shared.domain.tsid import TSID


class SqlAlchemyPageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, page: Page) -> Page:
        model = PageModel(
            id=page.id.value,
            owner_id=page.owner_id.value,
            parent_id=page.parent_id.value if page.parent_id else None,
            title=page.title,
            content=page.content,
            position=page.position,
        )
        self._session.add(model)
        await self._session.flush()
        return page

    async def update(self, page: Page) -> Page:
        statement = (
            update(PageModel)
            .where(
                PageModel.id == page.id.value,
                PageModel.owner_id == page.owner_id.value,
            )
            .values(title=page.title, content=page.content)
        )
        await self._session.execute(statement)
        await self._session.flush()
        return page

    async def find_owned_by_id(self, page_id: TSID, owner_id: TSID) -> Page | None:
        statement = select(PageModel).where(
            PageModel.id == page_id.value,
            PageModel.owner_id == owner_id.value,
        )
        model = await self._session.scalar(statement)
        return None if model is None else self._to_domain(model)

    async def list_by_owner(self, owner_id: TSID) -> list[Page]:
        statement = (
            select(PageModel)
            .where(PageModel.owner_id == owner_id.value)
            .order_by(PageModel.parent_id.nullsfirst(), PageModel.position, PageModel.id)
        )
        models = (await self._session.scalars(statement)).all()
        return [self._to_domain(model) for model in models]

    async def next_position(self, owner_id: TSID, parent_id: TSID | None) -> int:
        parent_filter = (
            PageModel.parent_id == parent_id.value
            if parent_id is not None
            else PageModel.parent_id.is_(None)
        )
        statement = select(func.coalesce(func.max(PageModel.position), -1) + 1).where(
            PageModel.owner_id == owner_id.value,
            parent_filter,
        )
        return int(await self._session.scalar(statement))

    @staticmethod
    def _to_domain(model: PageModel) -> Page:
        return Page(
            id=TSID(model.id),
            owner_id=TSID(model.owner_id),
            parent_id=TSID(model.parent_id) if model.parent_id is not None else None,
            title=model.title,
            content=model.content,
            position=model.position,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
