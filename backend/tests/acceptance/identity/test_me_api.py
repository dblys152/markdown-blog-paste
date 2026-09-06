from unittest.mock import AsyncMock

import httpx

from md2blog.main import create_app
from md2blog.modules.identity.domain.nickname_policy import NicknameAlreadyInUseError
from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import DisplayName, Email, PasswordHash
from md2blog.modules.identity.presentation.dependencies import (
    get_authenticate_access_token,
    get_update_display_name,
)
from md2blog.shared.domain.tsid import TSID


async def test_me_returns_authenticated_user() -> None:
    service = AsyncMock()
    service.execute.return_value = User(
        id=TSID(123456789),
        email=Email("user@example.com"),
        password_hash=PasswordHash("hidden"),
        display_name=DisplayName("User"),
    )
    app = create_app()
    app.dependency_overrides[get_authenticate_access_token] = lambda: service
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer access-token"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "id": "123456789",
        "email": "user@example.com",
        "display_name": "User",
        "email_verified": False,
    }


async def test_me_requires_bearer_token() -> None:
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/auth/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {
        "code": "AUTH_REQUIRED",
        "message": "로그인이 필요합니다.",
    }


async def test_update_me_changes_display_name() -> None:
    current_user = User(
        id=TSID(123456789),
        email=Email("user@example.com"),
        password_hash=PasswordHash("hidden"),
        display_name=DisplayName("기존 이름"),
    )
    authentication = AsyncMock()
    authentication.execute.return_value = current_user
    update_display_name = AsyncMock()
    update_display_name.execute.return_value = current_user.change_display_name(
        DisplayName("새 이름")
    )
    app = create_app()
    app.dependency_overrides[get_authenticate_access_token] = lambda: authentication
    app.dependency_overrides[get_update_display_name] = lambda: update_display_name
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            "/auth/me",
            headers={"Authorization": "Bearer access-token"},
            json={"display_name": "새 이름"},
        )

    assert response.status_code == 200
    assert response.json()["display_name"] == "새 이름"
    command = update_display_name.execute.await_args.args[1]
    assert command.display_name == DisplayName("새 이름")


async def test_update_me_rejects_blank_display_name() -> None:
    service = AsyncMock()
    service.execute.return_value = User(
        id=TSID(123456789),
        email=Email("user@example.com"),
        password_hash=PasswordHash("hidden"),
        display_name=DisplayName("User"),
    )
    app = create_app()
    app.dependency_overrides[get_authenticate_access_token] = lambda: service
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            "/auth/me",
            headers={"Authorization": "Bearer access-token"},
            json={"display_name": ""},
        )

    assert response.status_code == 422


async def test_update_me_rejects_duplicate_nickname() -> None:
    current_user = User(
        id=TSID(123456789),
        email=Email("user@example.com"),
        password_hash=PasswordHash("hidden"),
        display_name=DisplayName("기존 이름"),
    )
    authentication = AsyncMock()
    authentication.execute.return_value = current_user
    update_display_name = AsyncMock()
    update_display_name.execute.side_effect = NicknameAlreadyInUseError
    app = create_app()
    app.dependency_overrides[get_authenticate_access_token] = lambda: authentication
    app.dependency_overrides[get_update_display_name] = lambda: update_display_name
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            "/auth/me",
            headers={"Authorization": "Bearer access-token"},
            json={"display_name": "중복 닉네임"},
        )

    assert response.status_code == 409
    assert response.json() == {
        "code": "USER_NICKNAME_ALREADY_EXISTS",
        "message": "이미 사용 중인 닉네임입니다.",
    }
