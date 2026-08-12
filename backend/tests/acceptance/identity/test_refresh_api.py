from unittest.mock import AsyncMock

import httpx

from md2blog.main import create_app
from md2blog.modules.identity.application.service.refresh import TokenPairResult
from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import DisplayName, Email, PasswordHash
from md2blog.modules.identity.presentation.router import get_refresh_service
from md2blog.shared.domain.tsid import TSID


async def test_refresh_rotates_cookie_and_returns_access_token() -> None:
    service = AsyncMock()
    service.rotate.return_value = TokenPairResult(
        user=User(
            id=TSID(123456789),
            email=Email("user@example.com"),
            password_hash=PasswordHash("hidden"),
            display_name=DisplayName("User"),
        ),
        access_token="new-access-token",
        refresh_token="new-refresh-token",
    )
    app = create_app()
    app.dependency_overrides[get_refresh_service] = lambda: service
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
        cookies={"refresh_token": "old-refresh-token"},
    ) as client:
        response = await client.post("/auth/refresh")

    assert response.status_code == 200
    assert response.json()["access_token"] == "new-access-token"
    assert "refresh_token=new-refresh-token" in response.headers["set-cookie"]
    assert "HttpOnly" in response.headers["set-cookie"]
    service.rotate.assert_awaited_once()
