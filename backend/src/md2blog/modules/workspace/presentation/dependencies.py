from functools import lru_cache
from pathlib import Path

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from md2blog.modules.workspace.application.factory.pages import CreatePageCommandFactory
from md2blog.modules.workspace.application.port.outbound.object_storage import ObjectStorage
from md2blog.modules.workspace.application.service.pages import (
    CreatePage,
    CreatePdfPage,
    DeletePage,
    GetPage,
    GetPdfFile,
    GetTrashedPage,
    ListPages,
    ListTrashedPages,
    MovePage,
    PermanentlyDeletePage,
    RestorePage,
    SearchPages,
    UpdatePage,
)
from md2blog.modules.workspace.infrastructure.object_storage import (
    FileSystemObjectStorage,
    R2ObjectStorage,
)
from md2blog.modules.workspace.infrastructure.repositories import (
    SqlAlchemyPageQueryRepository,
    SqlAlchemyPageRepository,
)
from md2blog.settings import get_settings
from md2blog.shared.infrastructure.database import (
    SqlAlchemyUnitOfWork,
    get_session,
)


def get_create_page(
    session: AsyncSession = Depends(get_session),
) -> CreatePage:
    return CreatePage(
        SqlAlchemyPageRepository(session),
        SqlAlchemyUnitOfWork(session),
    )


@lru_cache
def get_object_storage() -> ObjectStorage:
    settings = get_settings()
    if settings.object_storage_backend == "r2":
        if not all(
            [
                settings.r2_endpoint_url,
                settings.r2_access_key_id,
                settings.r2_secret_access_key,
                settings.r2_bucket,
            ]
        ):
            raise RuntimeError("R2 object storage settings are incomplete")
        return R2ObjectStorage(
            endpoint_url=settings.r2_endpoint_url or "",
            access_key_id=settings.r2_access_key_id or "",
            secret_access_key=(
                settings.r2_secret_access_key.get_secret_value()
                if settings.r2_secret_access_key
                else ""
            ),
            bucket=settings.r2_bucket or "",
        )
    return FileSystemObjectStorage(Path(settings.object_storage_local_root))


def get_create_pdf_page(
    session: AsyncSession = Depends(get_session),
    storage: ObjectStorage = Depends(get_object_storage),
) -> CreatePdfPage:
    return CreatePdfPage(
        SqlAlchemyPageRepository(session),
        SqlAlchemyUnitOfWork(session),
        storage,
    )


def get_pdf_file(
    session: AsyncSession = Depends(get_session),
    storage: ObjectStorage = Depends(get_object_storage),
) -> GetPdfFile:
    return GetPdfFile(SqlAlchemyPageRepository(session), storage)


def get_create_page_command_factory(
    session: AsyncSession = Depends(get_session),
) -> CreatePageCommandFactory:
    return CreatePageCommandFactory(SqlAlchemyPageRepository(session))


def get_list_pages(session: AsyncSession = Depends(get_session)) -> ListPages:
    return ListPages(SqlAlchemyPageQueryRepository(session))


def get_search_pages(session: AsyncSession = Depends(get_session)) -> SearchPages:
    return SearchPages(SqlAlchemyPageQueryRepository(session))


def get_page(session: AsyncSession = Depends(get_session)) -> GetPage:
    return GetPage(SqlAlchemyPageQueryRepository(session))


def get_update_page(
    session: AsyncSession = Depends(get_session),
) -> UpdatePage:
    return UpdatePage(SqlAlchemyPageRepository(session), SqlAlchemyUnitOfWork(session))


def get_delete_page(
    session: AsyncSession = Depends(get_session),
) -> DeletePage:
    return DeletePage(SqlAlchemyPageRepository(session), SqlAlchemyUnitOfWork(session))


def get_move_page(
    session: AsyncSession = Depends(get_session),
) -> MovePage:
    return MovePage(SqlAlchemyPageRepository(session), SqlAlchemyUnitOfWork(session))


def get_list_trashed_pages(
    session: AsyncSession = Depends(get_session),
) -> ListTrashedPages:
    return ListTrashedPages(SqlAlchemyPageQueryRepository(session))


def get_trashed_page(session: AsyncSession = Depends(get_session)) -> GetTrashedPage:
    return GetTrashedPage(SqlAlchemyPageQueryRepository(session))


def get_restore_page(
    session: AsyncSession = Depends(get_session),
) -> RestorePage:
    return RestorePage(SqlAlchemyPageRepository(session), SqlAlchemyUnitOfWork(session))


def get_permanently_delete_page(
    session: AsyncSession = Depends(get_session),
) -> PermanentlyDeletePage:
    return PermanentlyDeletePage(
        SqlAlchemyPageRepository(session),
        SqlAlchemyUnitOfWork(session),
    )
