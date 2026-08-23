from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from md2blog.modules.workspace.application.factory.pages import CreatePageCommandFactory
from md2blog.modules.workspace.application.service.pages import (
    CreatePage,
    DeletePage,
    GetPage,
    GetTrashedPage,
    ListPages,
    ListTrashedPages,
    MovePage,
    PermanentlyDeletePage,
    RestorePage,
    UpdatePage,
)
from md2blog.modules.workspace.infrastructure.repositories import (
    SqlAlchemyPageQueryRepository,
    SqlAlchemyPageRepository,
)
from md2blog.shared.infrastructure.database import get_session


def get_create_page(session: AsyncSession = Depends(get_session)) -> CreatePage:
    return CreatePage(SqlAlchemyPageRepository(session))


def get_create_page_command_factory(
    session: AsyncSession = Depends(get_session),
) -> CreatePageCommandFactory:
    return CreatePageCommandFactory(SqlAlchemyPageRepository(session))


def get_list_pages(session: AsyncSession = Depends(get_session)) -> ListPages:
    return ListPages(SqlAlchemyPageQueryRepository(session))


def get_page(session: AsyncSession = Depends(get_session)) -> GetPage:
    return GetPage(SqlAlchemyPageQueryRepository(session))


def get_update_page(session: AsyncSession = Depends(get_session)) -> UpdatePage:
    return UpdatePage(SqlAlchemyPageRepository(session))


def get_delete_page(session: AsyncSession = Depends(get_session)) -> DeletePage:
    return DeletePage(SqlAlchemyPageRepository(session))


def get_move_page(session: AsyncSession = Depends(get_session)) -> MovePage:
    return MovePage(SqlAlchemyPageRepository(session))


def get_list_trashed_pages(
    session: AsyncSession = Depends(get_session),
) -> ListTrashedPages:
    return ListTrashedPages(SqlAlchemyPageQueryRepository(session))


def get_trashed_page(session: AsyncSession = Depends(get_session)) -> GetTrashedPage:
    return GetTrashedPage(SqlAlchemyPageQueryRepository(session))


def get_restore_page(session: AsyncSession = Depends(get_session)) -> RestorePage:
    return RestorePage(SqlAlchemyPageRepository(session))


def get_permanently_delete_page(
    session: AsyncSession = Depends(get_session),
) -> PermanentlyDeletePage:
    return PermanentlyDeletePage(SqlAlchemyPageRepository(session))
