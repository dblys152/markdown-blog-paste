from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.presentation.dependencies import get_current_user
from md2blog.modules.workspace.application.factory.pages import CreatePageCommandFactory
from md2blog.modules.workspace.application.port.inbound.pages import (
    CreatePageUseCase,
    DeletePageUseCase,
    GetPageUseCase,
    ListPagesUseCase,
    MovePageUseCase,
    SearchPagesUseCase,
    UpdatePageUseCase,
)
from md2blog.modules.workspace.domain.commands import (
    DeletePageCommand,
    MovePageCommand,
    UpdatePageCommand,
)
from md2blog.modules.workspace.presentation.dependencies import (
    get_create_page,
    get_create_page_command_factory,
    get_delete_page,
    get_list_pages,
    get_move_page,
    get_page,
    get_search_pages,
    get_update_page,
)
from md2blog.modules.workspace.presentation.schemas.pages import (
    CreatePageRequest,
    MovePageRequest,
    PageDetailResponse,
    PageListItemResponse,
    UpdatePageRequest,
)
from md2blog.shared.domain.tsid import TSID

router = APIRouter(prefix="/workspace/pages", tags=["workspace"])


@router.post("", response_model=PageDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_page(
    request: CreatePageRequest,
    current_user: User = Depends(get_current_user),
    command_factory: CreatePageCommandFactory = Depends(get_create_page_command_factory),
    use_case: CreatePageUseCase = Depends(get_create_page),
) -> PageDetailResponse:
    parent_id = TSID.from_string(request.parent_id) if request.parent_id else None
    command = await command_factory.create(
        owner_id=current_user.id,
        title=request.title,
        content=request.content,
        parent_id=parent_id,
    )
    page = await use_case.execute(command)
    return PageDetailResponse.from_model(page)


@router.get("", response_model=list[PageListItemResponse])
async def list_pages(
    current_user: User = Depends(get_current_user),
    use_case: ListPagesUseCase = Depends(get_list_pages),
) -> list[PageListItemResponse]:
    return [
        PageListItemResponse.from_model(page)
        for page in await use_case.execute(current_user.id)
    ]


@router.get("/search", response_model=list[PageListItemResponse])
async def search_pages(
    q: Annotated[str, Query(min_length=1, max_length=100)],
    current_user: User = Depends(get_current_user),
    use_case: SearchPagesUseCase = Depends(get_search_pages),
) -> list[PageListItemResponse]:
    return [
        PageListItemResponse.from_model(page)
        for page in await use_case.execute(owner_id=current_user.id, query=q)
    ]


@router.get("/{page_id}", response_model=PageDetailResponse)
async def get_page_detail(
    page_id: Annotated[int, Path(ge=0, le=2**63 - 1)],
    current_user: User = Depends(get_current_user),
    use_case: GetPageUseCase = Depends(get_page),
) -> PageDetailResponse:
    page = await use_case.execute(page_id=TSID(page_id), owner_id=current_user.id)
    return PageDetailResponse.from_model(page)


@router.patch("/{page_id}", response_model=PageDetailResponse)
async def update_page(
    page_id: Annotated[int, Path(ge=0, le=2**63 - 1)],
    request: UpdatePageRequest,
    current_user: User = Depends(get_current_user),
    use_case: UpdatePageUseCase = Depends(get_update_page),
) -> PageDetailResponse:
    page = await use_case.execute(
        UpdatePageCommand(
            page_id=TSID(page_id),
            owner_id=current_user.id,
            title=request.title,
            content=request.content,
        )
    )
    return PageDetailResponse.from_model(page)


@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_page(
    page_id: Annotated[int, Path(ge=0, le=2**63 - 1)],
    current_user: User = Depends(get_current_user),
    use_case: DeletePageUseCase = Depends(get_delete_page),
) -> None:
    await use_case.execute(
        DeletePageCommand(page_id=TSID(page_id), owner_id=current_user.id)
    )


@router.patch("/{page_id}/move", response_model=PageDetailResponse)
async def move_page(
    page_id: Annotated[int, Path(ge=0, le=2**63 - 1)],
    request: MovePageRequest,
    current_user: User = Depends(get_current_user),
    use_case: MovePageUseCase = Depends(get_move_page),
) -> PageDetailResponse:
    parent_id = TSID.from_string(request.parent_id) if request.parent_id else None
    page = await use_case.execute(
        MovePageCommand(
            page_id=TSID(page_id),
            owner_id=current_user.id,
            parent_id=parent_id,
            sort_order=request.sort_order,
        )
    )
    return PageDetailResponse.from_model(page)
