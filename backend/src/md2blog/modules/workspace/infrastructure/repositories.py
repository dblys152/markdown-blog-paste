from datetime import datetime, timedelta

from sqlalchemy import case, delete, func, insert, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from md2blog.modules.workspace.application.model.pages import (
    PageDetail,
    PageListItem,
    TrashedPageListItem,
)
from md2blog.modules.workspace.domain.page import Page, PageContent
from md2blog.modules.workspace.domain.page_types import PageType
from md2blog.modules.workspace.infrastructure.models import (
    PageContentModel,
    PageFileModel,
    PageModel,
)
from md2blog.shared.domain.tsid import TSID


class SqlAlchemyPageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, page: Page) -> None:
        await self._session.execute(
            insert(PageModel).values(
                id=page.id.value,
                owner_id=page.owner_id.value,
                parent_id=page.parent_id.value if page.parent_id else None,
                title=page.title,
                page_type=page.page_type.value,
                sort_order=page.sort_order,
                created_at=page.created_at,
                updated_at=page.updated_at,
                deleted_at=page.deleted_at,
            )
        )
        if page.content is not None:
            await self._session.execute(
                insert(PageContentModel).values(
                    page_id=page.id.value,
                    content=page.content.content,
                )
            )

    async def update(self, page: Page) -> None:
        statement = (
            update(PageModel)
            .where(
                PageModel.id == page.id.value,
                PageModel.owner_id == page.owner_id.value,
            )
            .values(
                title=page.title,
                page_type=page.page_type.value,
                parent_id=page.parent_id.value if page.parent_id else None,
                sort_order=page.sort_order,
                updated_at=page.updated_at,
                deleted_at=page.deleted_at,
            )
        )
        await self._session.execute(statement)
        if page.content is not None:
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
            PageModel.deleted_at.is_(None),
        ]
        if exclude_id is not None:
            filters.append(PageModel.id != exclude_id.value)
        statement = (
            select(PageModel, PageContentModel.content)
            .outerjoin(PageContentModel, PageContentModel.page_id == PageModel.id)
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
            .outerjoin(PageContentModel, PageContentModel.page_id == PageModel.id)
            .where(
                PageModel.id == page_id.value,
                PageModel.owner_id == owner_id.value,
                PageModel.deleted_at.is_(None),
            )
        )
        row = (await self._session.execute(statement)).one_or_none()
        return None if row is None else self._to_domain(row[0], row[1])

    async def find_trashed_by_id(self, page_id: TSID, owner_id: TSID) -> Page | None:
        statement = (
            select(PageModel, PageContentModel.content)
            .outerjoin(PageContentModel, PageContentModel.page_id == PageModel.id)
            .where(
                PageModel.id == page_id.value,
                PageModel.owner_id == owner_id.value,
                PageModel.deleted_at.is_not(None),
            )
        )
        row = (await self._session.execute(statement)).one_or_none()
        return None if row is None else self._to_domain(row[0], row[1])

    async def find_all_trashed_by_parent_id(
        self,
        owner_id: TSID,
        parent_id: TSID,
    ) -> list[Page]:
        statement = (
            select(PageModel, PageContentModel.content)
            .outerjoin(PageContentModel, PageContentModel.page_id == PageModel.id)
            .where(
                PageModel.owner_id == owner_id.value,
                PageModel.parent_id == parent_id.value,
                PageModel.deleted_at.is_not(None),
            )
            .order_by(PageModel.sort_order, PageModel.id)
        )
        rows = (await self._session.execute(statement)).all()
        return [self._to_domain(model, content) for model, content in rows]

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
                PageModel.deleted_at.is_(None),
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
                & (sibling.parent_id == parent.id)
                & sibling.deleted_at.is_(None),
            )
            .where(
                parent.id == parent_id.value,
                parent.owner_id == owner_id.value,
                parent.deleted_at.is_(None),
            )
            .group_by(parent.id)
        )
        value = await self._session.scalar(statement)
        return None if value is None else int(value)

    @staticmethod
    def _to_domain(model: PageModel, content: str | None) -> Page:
        return Page(
            id=TSID(model.id),
            owner_id=TSID(model.owner_id),
            parent_id=TSID(model.parent_id) if model.parent_id is not None else None,
            title=model.title,
            content=(
                PageContent(page_id=TSID(model.id), content=content)
                if content is not None
                else None
            ),
            sort_order=model.sort_order,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
            page_type=PageType(model.page_type),
        )

    async def delete_expired(self, threshold: datetime) -> int:
        page_ids = list(
            await self._session.scalars(
                select(PageModel.id).where(PageModel.deleted_at <= threshold)
            )
        )
        if not page_ids:
            return 0
        await self._session.execute(delete(PageModel).where(PageModel.id.in_(page_ids)))
        await self._session.flush()
        return len(page_ids)

    async def add_file(
        self,
        *,
        page_id: TSID,
        storage_key: str,
        original_filename: str,
        media_type: str,
        byte_size: int,
        checksum_sha256: str,
    ) -> None:
        await self._session.execute(
            insert(PageFileModel).values(
                page_id=page_id.value,
                storage_key=storage_key,
                original_filename=original_filename,
                media_type=media_type,
                byte_size=byte_size,
                checksum_sha256=checksum_sha256,
            )
        )

    async def total_file_bytes(self, owner_id: TSID) -> int:
        statement = (
            select(func.coalesce(func.sum(PageFileModel.byte_size), 0))
            .join(PageModel, PageModel.id == PageFileModel.page_id)
            .where(PageModel.owner_id == owner_id.value)
        )
        return int(await self._session.scalar(statement))

    async def find_file_key(self, page_id: TSID, owner_id: TSID) -> str | None:
        statement = (
            select(PageFileModel.storage_key)
            .join(PageModel, PageModel.id == PageFileModel.page_id)
            .where(PageModel.id == page_id.value, PageModel.owner_id == owner_id.value)
        )
        value = await self._session.scalar(statement)
        return str(value) if value is not None else None

    async def list_file_keys(self) -> set[str]:
        return set(await self._session.scalars(select(PageFileModel.storage_key)))


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
                PageModel.page_type,
            )
            .where(
                PageModel.owner_id == owner_id.value,
                PageModel.deleted_at.is_(None),
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
                page_type=PageType(row.page_type),
            )
            for row in rows
        ]

    async def search_by_owner_id(
        self,
        owner_id: TSID,
        query: str,
    ) -> list[PageListItem]:
        escaped_query = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped_query}%"
        title_matches = PageModel.title.ilike(pattern, escape="\\")
        content_matches = PageContentModel.content.ilike(pattern, escape="\\")
        statement = (
            select(
                PageModel.id,
                PageModel.owner_id,
                PageModel.parent_id,
                PageModel.title,
                PageModel.sort_order,
                PageModel.page_type,
            )
            .outerjoin(PageContentModel, PageContentModel.page_id == PageModel.id)
            .where(
                PageModel.owner_id == owner_id.value,
                PageModel.deleted_at.is_(None),
                or_(title_matches, content_matches),
            )
            .order_by(
                case((title_matches, 0), else_=1),
                PageModel.updated_at.desc(),
                PageModel.id,
            )
            .limit(50)
        )
        rows = (await self._session.execute(statement)).all()
        return [
            PageListItem(
                id=TSID(row.id),
                owner_id=TSID(row.owner_id),
                parent_id=TSID(row.parent_id) if row.parent_id is not None else None,
                title=row.title,
                sort_order=row.sort_order,
                page_type=PageType(row.page_type),
            )
            for row in rows
        ]

    async def find_detail_by_id(self, page_id: TSID, owner_id: TSID) -> PageDetail | None:
        statement = (
            select(PageModel, PageContentModel.content)
            .outerjoin(PageContentModel, PageContentModel.page_id == PageModel.id)
            .where(
                PageModel.id == page_id.value,
                PageModel.owner_id == owner_id.value,
                PageModel.deleted_at.is_(None),
            )
        )
        row = (await self._session.execute(statement)).one_or_none()
        if row is None:
            return None
        model, contents = row
        file_row = await self._session.execute(
            select(PageFileModel.original_filename, PageFileModel.byte_size).where(
                PageFileModel.page_id == model.id
            )
        )
        file_metadata = file_row.one_or_none()
        return PageDetail(
            id=TSID(model.id),
            owner_id=TSID(model.owner_id),
            parent_id=TSID(model.parent_id) if model.parent_id is not None else None,
            title=model.title,
            contents=contents,
            sort_order=model.sort_order,
            page_type=PageType(model.page_type),
            file_name=file_metadata.original_filename if file_metadata else None,
            file_size=file_metadata.byte_size if file_metadata else None,
        )

    async def find_all_trashed_by_owner_id(
        self,
        owner_id: TSID,
    ) -> list[TrashedPageListItem]:
        statement = (
            select(
                PageModel.id,
                PageModel.parent_id,
                PageModel.title,
                PageModel.sort_order,
                PageModel.deleted_at,
                PageModel.page_type,
            )
            .where(
                PageModel.owner_id == owner_id.value,
                PageModel.deleted_at.is_not(None),
            )
            .order_by(PageModel.deleted_at.desc(), PageModel.sort_order, PageModel.id)
        )
        rows = (await self._session.execute(statement)).all()
        return [
            TrashedPageListItem(
                id=TSID(row.id),
                parent_id=TSID(row.parent_id) if row.parent_id is not None else None,
                title=row.title,
                sort_order=row.sort_order,
                deleted_at=row.deleted_at,
                expires_at=row.deleted_at + timedelta(days=30),
                page_type=PageType(row.page_type),
            )
            for row in rows
            if row.deleted_at is not None
        ]

    async def find_trashed_detail_by_id(
        self,
        page_id: TSID,
        owner_id: TSID,
    ) -> PageDetail | None:
        statement = (
            select(PageModel, PageContentModel.content)
            .outerjoin(PageContentModel, PageContentModel.page_id == PageModel.id)
            .where(
                PageModel.id == page_id.value,
                PageModel.owner_id == owner_id.value,
                PageModel.deleted_at.is_not(None),
            )
        )
        row = (await self._session.execute(statement)).one_or_none()
        if row is None:
            return None
        model, contents = row
        file_row = await self._session.execute(
            select(PageFileModel.original_filename, PageFileModel.byte_size).where(
                PageFileModel.page_id == model.id
            )
        )
        file_metadata = file_row.one_or_none()
        return PageDetail(
            id=TSID(model.id),
            owner_id=TSID(model.owner_id),
            parent_id=TSID(model.parent_id) if model.parent_id is not None else None,
            title=model.title,
            contents=contents,
            sort_order=model.sort_order,
            page_type=PageType(model.page_type),
            file_name=file_metadata.original_filename if file_metadata else None,
            file_size=file_metadata.byte_size if file_metadata else None,
        )
