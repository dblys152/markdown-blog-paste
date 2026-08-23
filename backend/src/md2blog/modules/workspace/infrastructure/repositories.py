from sqlalchemy import delete, func, insert, literal, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from md2blog.modules.workspace.application.model.pages import PageDetail, PageListItem
from md2blog.modules.workspace.domain.page import Page, PageContent
from md2blog.modules.workspace.infrastructure.models import PageContentModel, PageModel
from md2blog.shared.domain.tsid import TSID


class SqlAlchemyPageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, page: Page) -> None:
        inserted_page = (
            insert(PageModel)
            .values(
                id=page.id.value,
                owner_id=page.owner_id.value,
                parent_id=page.parent_id.value if page.parent_id else None,
                title=page.title,
                sort_order=page.sort_order,
                created_at=page.created_at,
                updated_at=page.updated_at,
            )
            .returning(PageModel.id)
            .cte("inserted_page")
        )
        statement = insert(PageContentModel).from_select(
            [PageContentModel.page_id, PageContentModel.content],
            select(inserted_page.c.id, literal(page.content.content)),
        )
        await self._session.execute(statement)

    async def update(self, page: Page) -> None:
        statement = (
            update(PageModel)
            .where(
                PageModel.id == page.id.value,
                PageModel.owner_id == page.owner_id.value,
            )
            .values(
                title=page.title,
                parent_id=page.parent_id.value if page.parent_id else None,
                sort_order=page.sort_order,
                updated_at=page.updated_at,
            )
        )
        await self._session.execute(statement)
        content_statement = (
            update(PageContentModel)
            .where(PageContentModel.page_id == page.content.page_id.value)
            .values(content=page.content.content)
        )
        await self._session.execute(content_statement)
        await self._session.flush()

    async def update_all(self, pages: list[Page]) -> None:
        for page in pages:
            await self.update(page)

    async def delete(self, page: Page) -> None:
        statement = delete(PageModel).where(
            PageModel.id == page.id.value,
            PageModel.owner_id == page.owner_id.value,
        )
        await self._session.execute(statement)
        await self._session.flush()

    async def find_all_by_parent_id(
        self,
        owner_id: TSID,
        parent_id: TSID | None,
        *,
        exclude_id: TSID | None = None,
    ) -> list[Page]:
        parent_filter = (
            PageModel.parent_id == parent_id.value
            if parent_id is not None
            else PageModel.parent_id.is_(None)
        )
        filters = [
            PageModel.owner_id == owner_id.value,
            parent_filter,
        ]
        if exclude_id is not None:
            filters.append(PageModel.id != exclude_id.value)
        statement = (
            select(PageModel, PageContentModel.content)
            .join(PageContentModel, PageContentModel.page_id == PageModel.id)
            .where(
                *filters,
            )
            .order_by(PageModel.sort_order, PageModel.id)
            .with_for_update()
        )
        rows = (await self._session.execute(statement)).all()
        return [self._to_domain(model, content) for model, content in rows]

    async def find_by_id(self, page_id: TSID, owner_id: TSID) -> Page | None:
        statement = (
            select(PageModel, PageContentModel.content)
            .join(PageContentModel, PageContentModel.page_id == PageModel.id)
            .where(
                PageModel.id == page_id.value,
                PageModel.owner_id == owner_id.value,
            )
        )
        row = (await self._session.execute(statement)).one_or_none()
        return None if row is None else self._to_domain(row[0], row[1])

    async def next_sort_order(
        self,
        owner_id: TSID,
        parent_id: TSID | None,
    ) -> int | None:
        if parent_id is None:
            statement = select(
                func.coalesce(func.max(PageModel.sort_order), -1) + 1
            ).where(
                PageModel.owner_id == owner_id.value,
                PageModel.parent_id.is_(None),
            )
            return int(await self._session.scalar(statement))

        parent = aliased(PageModel)
        sibling = aliased(PageModel)
        statement = (
            select(func.coalesce(func.max(sibling.sort_order), -1) + 1)
            .select_from(parent)
            .outerjoin(
                sibling,
                (sibling.owner_id == owner_id.value)
                & (sibling.parent_id == parent.id),
            )
            .where(
                parent.id == parent_id.value,
                parent.owner_id == owner_id.value,
            )
            .group_by(parent.id)
        )
        value = await self._session.scalar(statement)
        return None if value is None else int(value)

    @staticmethod
    def _to_domain(model: PageModel, content: str) -> Page:
        return Page(
            id=TSID(model.id),
            owner_id=TSID(model.owner_id),
            parent_id=TSID(model.parent_id) if model.parent_id is not None else None,
            title=model.title,
            content=PageContent(page_id=TSID(model.id), content=content),
            sort_order=model.sort_order,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class SqlAlchemyPageQueryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_all_by_owner_id(self, owner_id: TSID) -> list[PageListItem]:
        statement = (
            select(
                PageModel.id,
                PageModel.owner_id,
                PageModel.parent_id,
                PageModel.title,
                PageModel.sort_order,
            )
            .where(
                PageModel.owner_id == owner_id.value,
            )
            .order_by(PageModel.parent_id.nullsfirst(), PageModel.sort_order, PageModel.id)
        )
        rows = (await self._session.execute(statement)).all()
        return [
            PageListItem(
                id=TSID(row.id),
                owner_id=TSID(row.owner_id),
                parent_id=TSID(row.parent_id) if row.parent_id is not None else None,
                title=row.title,
                sort_order=row.sort_order,
            )
            for row in rows
        ]

    async def find_detail_by_id(self, page_id: TSID, owner_id: TSID) -> PageDetail | None:
        statement = (
            select(PageModel, PageContentModel.content)
            .join(PageContentModel, PageContentModel.page_id == PageModel.id)
            .where(
                PageModel.id == page_id.value,
                PageModel.owner_id == owner_id.value,
            )
        )
        row = (await self._session.execute(statement)).one_or_none()
        if row is None:
            return None
        model, contents = row
        return PageDetail(
            id=TSID(model.id),
            owner_id=TSID(model.owner_id),
            parent_id=TSID(model.parent_id) if model.parent_id is not None else None,
            title=model.title,
            contents=contents,
            sort_order=model.sort_order,
        )
