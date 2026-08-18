from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from md2blog.modules.workspace.application.service.pages import CreatePage, ListPages
from md2blog.modules.workspace.infrastructure.repositories import SqlAlchemyPageRepository
from md2blog.shared.infrastructure.database import get_session


def get_create_page(session: AsyncSession = Depends(get_session)) -> CreatePage:
    return CreatePage(SqlAlchemyPageRepository(session))


def get_list_pages(session: AsyncSession = Depends(get_session)) -> ListPages:
    return ListPages(SqlAlchemyPageRepository(session))
