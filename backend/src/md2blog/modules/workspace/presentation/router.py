from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.presentation.dependencies import get_current_user
from md2blog.modules.workspace.application.port.inbound.pages import (
    CreatePageRequest,
    CreatePageUseCase,
    DeletePageUseCase,
    ListPagesUseCase,
    MovePageRequest,
    MovePageUseCase,
    PageResponse,
    UpdatePageRequest,
    UpdatePageUseCase,
)
from md2blog.modules.workspace.presentation.dependencies import (
    get_create_page,
    get_delete_page,
    get_list_pages,
    get_move_page,
    get_update_page,
)
from md2blog.shared.domain.tsid import TSID

router = APIRouter(prefix="/workspace/pages", tags=["workspace"])


@router.post("", response_model=PageResponse, status_code=status.HTTP_201_CREATED)
async def create_page(
    request: CreatePageRequest,
    current_user: User = Depends(get_current_user),
    use_case: CreatePageUseCase = Depends(get_create_page),
) -> PageResponse:
    parent_id = TSID.from_string(request.parent_id) if request.parent_id else None
    page = await use_case.execute(
        owner_id=current_user.id,
        title=request.title,
        content=request.content,
        parent_id=parent_id,
    )
    return PageResponse.from_domain(page)


@router.get("", response_model=list[PageResponse])
async def list_pages(
    current_user: User = Depends(get_current_user),
    use_case: ListPagesUseCase = Depends(get_list_pages),
) -> list[PageResponse]:
    return [PageResponse.from_domain(page) for page in await use_case.execute(current_user.id)]


@router.patch("/{page_id}", response_model=PageResponse)
async def update_page(
    page_id: Annotated[int, Path(ge=0, le=2**63 - 1)],
    request: UpdatePageRequest,
    current_user: User = Depends(get_current_user),
    use_case: UpdatePageUseCase = Depends(get_update_page),
) -> PageResponse:
    page = await use_case.execute(
        page_id=TSID(page_id),
        owner_id=current_user.id,
        title=request.title,
        content=request.content,
    )
    return PageResponse.from_domain(page)


@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_page(
    page_id: Annotated[int, Path(ge=0, le=2**63 - 1)],
    current_user: User = Depends(get_current_user),
    use_case: DeletePageUseCase = Depends(get_delete_page),
) -> None:
    await use_case.execute(page_id=TSID(page_id), owner_id=current_user.id)


@router.patch("/{page_id}/move", response_model=PageResponse)
async def move_page(
    page_id: Annotated[int, Path(ge=0, le=2**63 - 1)],
    request: MovePageRequest,
    current_user: User = Depends(get_current_user),
    use_case: MovePageUseCase = Depends(get_move_page),
) -> PageResponse:
    parent_id = TSID.from_string(request.parent_id) if request.parent_id else None
    page = await use_case.execute(
        page_id=TSID(page_id),
        owner_id=current_user.id,
        parent_id=parent_id,
        position=request.position,
    )
    return PageResponse.from_domain(page)
