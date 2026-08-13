from unittest.mock import AsyncMock

import httpx

from md2blog.main import create_app
from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import DisplayName, Email, PasswordHash
from md2blog.modules.identity.presentation.dependencies import (
    get_authenticate_access_token,
    get_logout_service,
)
from md2blog.shared.domain.tsid import TSID


async def test_logout_revokes_session_and_deletes_cookie() -> None:
    service = AsyncMock()
    app = create_app()
    app.dependency_overrides[get_logout_service] = lambda: service
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
        cookies={"refresh_token": "refresh-token"},
    ) as client:
        response = await client.post("/auth/logout")

    assert response.status_code == 204
    assert response.content == b""
    assert "refresh_token=" in response.headers["set-cookie"]
    assert "Max-Age=0" in response.headers["set-cookie"]
    service.logout.assert_awaited_once_with("refresh-token")


async def test_logout_all_requires_authentication_and_deletes_cookie() -> None:
    user = User(
        id=TSID(123456789),
        email=Email("user@example.com"),
        password_hash=PasswordHash("hidden"),
        display_name=DisplayName("User"),
    )
    authentication = AsyncMock()
    authentication.execute.return_value = user
    logout_service = AsyncMock()
    app = create_app()
    app.dependency_overrides[get_authenticate_access_token] = lambda: authentication
    app.dependency_overrides[get_logout_service] = lambda: logout_service
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/auth/logout-all",
            headers={"Authorization": "Bearer access-token"},
        )

    assert response.status_code == 204
    assert response.content == b""
    assert "Max-Age=0" in response.headers["set-cookie"]
    logout_service.logout_all.assert_awaited_once_with(user.id)
