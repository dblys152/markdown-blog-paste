from datetime import UTC, datetime
from unittest.mock import AsyncMock

import httpx

from md2blog.main import create_app
from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import DisplayName, Email, PasswordHash
from md2blog.modules.identity.presentation.dependencies import get_current_user
from md2blog.modules.workspace.application.model.pages import (
    PageDetail,
    PageListItem,
    TrashedPageListItem,
)
from md2blog.modules.workspace.domain.commands import (
    CreatePageCommand,
    DeletePageCommand,
    MovePageCommand,
    PermanentlyDeletePageCommand,
    RestorePageCommand,
    UpdatePageCommand,
)
from md2blog.modules.workspace.presentation.dependencies import (
    get_create_page,
    get_create_page_command_factory,
    get_delete_page,
    get_list_pages,
    get_list_trashed_pages,
    get_move_page,
    get_page,
    get_permanently_delete_page,
    get_restore_page,
    get_search_pages,
    get_trashed_page,
    get_update_page,
)
from md2blog.shared.domain.tsid import TSID


def authenticated_user() -> User:
    return User(
        id=TSID(1),
        email=Email("user@example.com"),
        password_hash=PasswordHash("hidden"),
        display_name=DisplayName("User"),
    )


async def test_create_page_uses_authenticated_user() -> None:
    page = PageDetail(
        id=TSID(2),
        owner_id=TSID(1),
        parent_id=None,
        title="개발 노트",
        contents="# 개발 노트",
        sort_order=0,
    )
    use_case = AsyncMock()
    use_case.execute.return_value = page
    command = CreatePageCommand(
        owner_id=TSID(1),
        title="개발 노트",
        content="# 개발 노트",
        parent_id=None,
        sort_order=0,
    )
    command_factory = AsyncMock()
    command_factory.create.return_value = command
    app = create_app()
    app.dependency_overrides[get_current_user] = authenticated_user
    app.dependency_overrides[get_create_page] = lambda: use_case
    app.dependency_overrides[get_create_page_command_factory] = lambda: command_factory

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/workspace/pages",
            json={"title": "개발 노트", "content": "# 개발 노트"},
        )

    assert response.status_code == 201
    assert response.json() == {
        "id": "2",
        "owner_id": "1",
        "title": "개발 노트",
        "contents": "# 개발 노트",
        "parent_id": None,
        "sort_order": 0,
    }
    command_factory.create.assert_awaited_once_with(
        owner_id=TSID(1), title="개발 노트", content="# 개발 노트", parent_id=None
    )
    use_case.execute.assert_awaited_once_with(command)


async def test_list_pages_returns_flat_ordered_collection() -> None:
    use_case = AsyncMock()
    use_case.execute.return_value = [
        PageListItem(
            id=TSID(2), owner_id=TSID(1), parent_id=None, title="개발 노트", sort_order=0
        ),
        PageListItem(
            id=TSID(3),
            owner_id=TSID(1),
            parent_id=TSID(2),
            title="API 설계",
            sort_order=0,
        ),
    ]
    app = create_app()
    app.dependency_overrides[get_current_user] = authenticated_user
    app.dependency_overrides[get_list_pages] = lambda: use_case

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/workspace/pages")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == ["2", "3"]
    assert all("contents" not in item for item in response.json())


async def test_get_page_returns_markdown_content() -> None:
    use_case = AsyncMock()
    use_case.execute.return_value = PageDetail(
        id=TSID(2),
        owner_id=TSID(1),
        title="개발 노트",
        contents="# 개발 노트",
        parent_id=None,
        sort_order=0,
    )
    app = create_app()
    app.dependency_overrides[get_current_user] = authenticated_user
    app.dependency_overrides[get_page] = lambda: use_case

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/workspace/pages/2")

    assert response.status_code == 200
    assert response.json()["contents"] == "# 개발 노트"
    use_case.execute.assert_awaited_once_with(page_id=TSID(2), owner_id=TSID(1))


async def test_pages_require_authentication() -> None:
    app = create_app()

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/workspace/pages")

    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_REQUIRED"


async def test_create_page_rejects_invalid_parent_id() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user] = authenticated_user

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/workspace/pages",
            json={"title": "하위 페이지", "parent_id": "not-a-tsid"},
        )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


async def test_update_page_supports_markdown_autosave() -> None:
    use_case = AsyncMock()
    use_case.execute.return_value = PageDetail(
        id=TSID(2),
        owner_id=TSID(1),
        title="개발 노트",
        contents="# 자동 저장된 본문",
        parent_id=None,
        sort_order=0,
    )
    app = create_app()
    app.dependency_overrides[get_current_user] = authenticated_user
    app.dependency_overrides[get_update_page] = lambda: use_case

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.patch(
            "/workspace/pages/2",
            json={"content": "# 자동 저장된 본문"},
        )

    assert response.status_code == 200
    assert response.json()["contents"] == "# 자동 저장된 본문"
    use_case.execute.assert_awaited_once_with(
        UpdatePageCommand(
            page_id=TSID(2),
            owner_id=TSID(1),
            title=None,
            content="# 자동 저장된 본문",
        )
    )


async def test_update_page_rejects_empty_change_set() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user] = authenticated_user

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.patch("/workspace/pages/2", json={})

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


async def test_update_page_rejects_invalid_page_id() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user] = authenticated_user

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.patch(
            "/workspace/pages/not-a-tsid",
            json={"content": "# 본문"},
        )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


async def test_delete_page_returns_no_content() -> None:
    use_case = AsyncMock()
    app = create_app()
    app.dependency_overrides[get_current_user] = authenticated_user
    app.dependency_overrides[get_delete_page] = lambda: use_case

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete("/workspace/pages/2")

    assert response.status_code == 204
    assert response.content == b""
    use_case.execute.assert_awaited_once_with(
        DeletePageCommand(page_id=TSID(2), owner_id=TSID(1))
    )


async def test_delete_page_requires_authentication() -> None:
    app = create_app()

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete("/workspace/pages/2")

    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_REQUIRED"


async def test_search_pages_uses_authenticated_user_and_query() -> None:
    use_case = AsyncMock()
    use_case.execute.return_value = [
        PageListItem(
            id=TSID(2),
            owner_id=TSID(1),
            parent_id=TSID(3),
            title="API 설계",
            sort_order=0,
        )
    ]
    app = create_app()
    app.dependency_overrides[get_current_user] = authenticated_user
    app.dependency_overrides[get_search_pages] = lambda: use_case

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/workspace/pages/search", params={"q": "API"})

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "2",
            "owner_id": "1",
            "parent_id": "3",
            "title": "API 설계",
            "sort_order": 0,
        }
    ]
    use_case.execute.assert_awaited_once_with(owner_id=TSID(1), query="API")


async def test_move_page_accepts_root_destination() -> None:
    use_case = AsyncMock()
    use_case.execute.return_value = PageDetail(
        id=TSID(2),
        owner_id=TSID(1),
        title="이동한 페이지",
        contents="",
        parent_id=None,
        sort_order=1,
    )
    app = create_app()
    app.dependency_overrides[get_current_user] = authenticated_user
    app.dependency_overrides[get_move_page] = lambda: use_case

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.patch(
            "/workspace/pages/2/move",
            json={"parent_id": None, "sort_order": 1},
        )

    assert response.status_code == 200
    assert response.json()["parent_id"] is None
    assert response.json()["sort_order"] == 1
    use_case.execute.assert_awaited_once_with(
        MovePageCommand(
            page_id=TSID(2),
            owner_id=TSID(1),
            parent_id=None,
            sort_order=1,
        )
    )


async def test_move_page_requires_destination_parent_field() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user] = authenticated_user

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.patch(
            "/workspace/pages/2/move",
            json={"sort_order": 0},
        )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


async def test_list_trash_returns_expiration_date() -> None:
    deleted_at = datetime(2026, 1, 1, tzinfo=UTC)
    expires_at = datetime(2026, 1, 31, tzinfo=UTC)
    use_case = AsyncMock()
    use_case.execute.return_value = [
        TrashedPageListItem(
            id=TSID(2),
            parent_id=None,
            title="삭제한 페이지",
            sort_order=0,
            deleted_at=deleted_at,
            expires_at=expires_at,
        )
    ]
    app = create_app()
    app.dependency_overrides[get_current_user] = authenticated_user
    app.dependency_overrides[get_list_trashed_pages] = lambda: use_case

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/workspace/trash")

    assert response.status_code == 200
    assert response.json()[0]["title"] == "삭제한 페이지"
    assert response.json()[0]["parent_id"] is None
    assert response.json()[0]["sort_order"] == 0
    assert response.json()[0]["expires_at"] == "2026-01-31T00:00:00Z"
    use_case.execute.assert_awaited_once_with(TSID(1))


async def test_get_trashed_page_returns_markdown_content() -> None:
    use_case = AsyncMock()
    use_case.execute.return_value = PageDetail(
        id=TSID(2),
        owner_id=TSID(1),
        parent_id=None,
        title="삭제한 페이지",
        contents="# 삭제한 페이지",
        sort_order=0,
    )
    app = create_app()
    app.dependency_overrides[get_current_user] = authenticated_user
    app.dependency_overrides[get_trashed_page] = lambda: use_case

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/workspace/trash/2")

    assert response.status_code == 200
    assert response.json()["contents"] == "# 삭제한 페이지"
    use_case.execute.assert_awaited_once_with(page_id=TSID(2), owner_id=TSID(1))


async def test_restore_trashed_page_returns_no_content() -> None:
    use_case = AsyncMock()
    app = create_app()
    app.dependency_overrides[get_current_user] = authenticated_user
    app.dependency_overrides[get_restore_page] = lambda: use_case

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/workspace/trash/2/restore")

    assert response.status_code == 204
    use_case.execute.assert_awaited_once_with(
        RestorePageCommand(page_id=TSID(2), owner_id=TSID(1))
    )


async def test_permanently_delete_trashed_page_returns_no_content() -> None:
    use_case = AsyncMock()
    app = create_app()
    app.dependency_overrides[get_current_user] = authenticated_user
    app.dependency_overrides[get_permanently_delete_page] = lambda: use_case

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete("/workspace/trash/2")

    assert response.status_code == 204
    use_case.execute.assert_awaited_once_with(
        PermanentlyDeletePageCommand(page_id=TSID(2), owner_id=TSID(1))
    )
