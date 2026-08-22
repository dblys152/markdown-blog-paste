from typing import Protocol

from md2blog.modules.workspace.application.model.pages import PageDetail, PageListItem
from md2blog.modules.workspace.domain.commands import (
    CreatePageCommand,
    DeletePageCommand,
    MovePageCommand,
    UpdatePageCommand,
)
from md2blog.shared.domain.tsid import TSID


class CreatePageUseCase(Protocol):
    async def execute(self, command: CreatePageCommand) -> PageDetail: ...


class ListPagesUseCase(Protocol):
    async def execute(self, owner_id: TSID) -> list[PageListItem]: ...


class GetPageUseCase(Protocol):
    async def execute(self, *, page_id: TSID, owner_id: TSID) -> PageDetail: ...


class UpdatePageUseCase(Protocol):
    async def execute(self, command: UpdatePageCommand) -> PageDetail: ...


class DeletePageUseCase(Protocol):
    async def execute(self, command: DeletePageCommand) -> None: ...


class MovePageUseCase(Protocol):
    async def execute(self, command: MovePageCommand) -> PageDetail: ...
