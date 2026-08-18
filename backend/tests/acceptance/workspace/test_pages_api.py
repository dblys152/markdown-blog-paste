from unittest.mock import AsyncMock

import httpx

from md2blog.main import create_app
from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import DisplayName, Email, PasswordHash
from md2blog.modules.identity.presentation.dependencies import get_current_user
from md2blog.modules.workspace.domain.page import Page
from md2blog.modules.workspace.presentation.dependencies import (
    get_create_page,
    get_list_pages,
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
    page = Page(
        id=TSID(2),
        owner_id=TSID(1),
        parent_id=None,
        title="개발 노트",
        content="# 개발 노트",
    )
    use_case = AsyncMock()
    use_case.execute.return_value = page
    app = create_app()
    app.dependency_overrides[get_current_user] = authenticated_user
    app.dependency_overrides[get_create_page] = lambda: use_case

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
        "title": "개발 노트",
        "content": "# 개발 노트",
        "parent_id": None,
        "position": 0,
    }
    use_case.execute.assert_awaited_once_with(
        owner_id=TSID(1), title="개발 노트", content="# 개발 노트", parent_id=None
    )


async def test_list_pages_returns_flat_ordered_collection() -> None:
    use_case = AsyncMock()
    use_case.execute.return_value = [
        Page(id=TSID(2), owner_id=TSID(1), title="개발 노트", content=""),
        Page(
            id=TSID(3),
            owner_id=TSID(1),
            parent_id=TSID(2),
            title="API 설계",
            content="",
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
    use_case.execute.return_value = Page(
        id=TSID(2),
        owner_id=TSID(1),
        title="개발 노트",
        content="# 자동 저장된 본문",
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
    assert response.json()["content"] == "# 자동 저장된 본문"
    use_case.execute.assert_awaited_once_with(
        page_id=TSID(2),
        owner_id=TSID(1),
        title=None,
        content="# 자동 저장된 본문",
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
