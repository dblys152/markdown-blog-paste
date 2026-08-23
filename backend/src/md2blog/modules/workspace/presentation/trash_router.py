from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.presentation.dependencies import get_current_user
from md2blog.modules.workspace.application.port.inbound.pages import (
    GetTrashedPageUseCase,
    ListTrashedPagesUseCase,
    PermanentlyDeletePageUseCase,
    RestorePageUseCase,
)
from md2blog.modules.workspace.domain.commands import (
    PermanentlyDeletePageCommand,
    RestorePageCommand,
)
from md2blog.modules.workspace.presentation.dependencies import (
    get_list_trashed_pages,
    get_permanently_delete_page,
    get_restore_page,
    get_trashed_page,
)
from md2blog.modules.workspace.presentation.schemas.pages import (
    PageDetailResponse,
    TrashedPageListItemResponse,
)
from md2blog.shared.domain.tsid import TSID

router = APIRouter(prefix="/workspace/trash", tags=["workspace-trash"])


@router.get("", response_model=list[TrashedPageListItemResponse])
async def list_trashed_pages(
    current_user: User = Depends(get_current_user),
    use_case: ListTrashedPagesUseCase = Depends(get_list_trashed_pages),
) -> list[TrashedPageListItemResponse]:
    return [
        TrashedPageListItemResponse.from_model(page)
        for page in await use_case.execute(current_user.id)
    ]


@router.get("/{page_id}", response_model=PageDetailResponse)
async def get_trashed_page_detail(
    page_id: Annotated[int, Path(ge=0, le=2**63 - 1)],
    current_user: User = Depends(get_current_user),
    use_case: GetTrashedPageUseCase = Depends(get_trashed_page),
) -> PageDetailResponse:
    page = await use_case.execute(page_id=TSID(page_id), owner_id=current_user.id)
    return PageDetailResponse.from_model(page)


@router.post("/{page_id}/restore", status_code=status.HTTP_204_NO_CONTENT)
async def restore_page(
    page_id: Annotated[int, Path(ge=0, le=2**63 - 1)],
    current_user: User = Depends(get_current_user),
    use_case: RestorePageUseCase = Depends(get_restore_page),
) -> None:
    await use_case.execute(
        RestorePageCommand(page_id=TSID(page_id), owner_id=current_user.id)
    )


@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def permanently_delete_page(
    page_id: Annotated[int, Path(ge=0, le=2**63 - 1)],
    current_user: User = Depends(get_current_user),
    use_case: PermanentlyDeletePageUseCase = Depends(get_permanently_delete_page),
) -> None:
    await use_case.execute(
        PermanentlyDeletePageCommand(page_id=TSID(page_id), owner_id=current_user.id)
    )
