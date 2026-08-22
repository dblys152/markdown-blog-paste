from collections.abc import Sequence

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from md2blog.modules.workspace.domain.page import Page, PageListItem
from md2blog.modules.workspace.infrastructure.models import PageContentModel, PageModel
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
            position=page.position,
        )
        self._session.add(model)
        await self._session.flush()
        self._session.add(PageContentModel(page_id=page.id.value, content=page.content))
        await self._session.flush()
        return page

    async def update(
        self,
        page: Page,
        *,
        title_changed: bool,
        content_changed: bool,
    ) -> Page:
        if title_changed:
            page_statement = (
                update(PageModel)
                .where(
                    PageModel.id == page.id.value,
                    PageModel.owner_id == page.owner_id.value,
                )
                .values(title=page.title)
            )
            await self._session.execute(page_statement)
        if content_changed:
            content_statement = (
                update(PageContentModel)
                .where(PageContentModel.page_id == page.id.value)
                .values(content=page.content)
            )
            await self._session.execute(content_statement)
        await self._session.flush()
        return page

    async def delete(self, page: Page) -> None:
        statement = delete(PageModel).where(
            PageModel.id == page.id.value,
            PageModel.owner_id == page.owner_id.value,
        )
        await self._session.execute(statement)
        await self._session.flush()

    async def move(self, page: Page, parent_id: TSID | None, position: int) -> Page:
        old_parent_id = page.parent_id
        old_siblings = await self._sibling_models(page.owner_id, old_parent_id, exclude_id=page.id)
        if old_parent_id == parent_id:
            target_siblings: list[PageModel | None] = list(old_siblings)
        else:
            target_siblings = list(
                await self._sibling_models(
                    page.owner_id,
                    parent_id,
                    exclude_id=page.id,
                )
            )

        target_position = min(position, len(target_siblings))
        target_siblings.insert(target_position, None)

        if old_parent_id != parent_id:
            await self._write_positions(old_siblings)
        await self._write_positions(target_siblings, moving_page=page, parent_id=parent_id)
        await self._session.flush()
        return page.move_to(parent_id=parent_id, position=target_position)

    async def _sibling_models(
        self,
        owner_id: TSID,
        parent_id: TSID | None,
        *,
        exclude_id: TSID,
    ) -> list[PageModel]:
        parent_filter = (
            PageModel.parent_id == parent_id.value
            if parent_id is not None
            else PageModel.parent_id.is_(None)
        )
        statement = (
            select(PageModel)
            .where(
                PageModel.owner_id == owner_id.value,
                parent_filter,
                PageModel.id != exclude_id.value,
            )
            .order_by(PageModel.position, PageModel.id)
            .with_for_update()
        )
        return list((await self._session.scalars(statement)).all())

    async def _write_positions(
        self,
        siblings: Sequence[PageModel | None],
        *,
        moving_page: Page | None = None,
        parent_id: TSID | None = None,
    ) -> None:
        for index, sibling in enumerate(siblings):
            if sibling is None:
                if moving_page is None:
                    continue
                statement = (
                    update(PageModel)
                    .where(
                        PageModel.id == moving_page.id.value,
                        PageModel.owner_id == moving_page.owner_id.value,
                    )
                    .values(
                        parent_id=parent_id.value if parent_id is not None else None,
                        position=index,
                    )
                )
                await self._session.execute(statement)
            elif sibling.position != index:
                sibling.position = index

    async def find_owned_by_id(self, page_id: TSID, owner_id: TSID) -> Page | None:
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

    async def list_by_owner(self, owner_id: TSID) -> list[PageListItem]:
        statement = (
            select(
                PageModel.id,
                PageModel.owner_id,
                PageModel.parent_id,
                PageModel.title,
                PageModel.position,
                PageModel.created_at,
                PageModel.updated_at,
            )
            .where(PageModel.owner_id == owner_id.value)
            .order_by(PageModel.parent_id.nullsfirst(), PageModel.position, PageModel.id)
        )
        rows = (await self._session.execute(statement)).all()
        return [
            PageListItem(
                id=TSID(row.id),
                owner_id=TSID(row.owner_id),
                parent_id=TSID(row.parent_id) if row.parent_id is not None else None,
                title=row.title,
                position=row.position,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ]

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
    def _to_domain(model: PageModel, content: str) -> Page:
        return Page(
            id=TSID(model.id),
            owner_id=TSID(model.owner_id),
            parent_id=TSID(model.parent_id) if model.parent_id is not None else None,
            title=model.title,
            content=content,
            position=model.position,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
