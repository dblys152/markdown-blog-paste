from unittest.mock import AsyncMock

import httpx

from md2blog.main import create_app
from md2blog.modules.identity.application.service.login import LoginResult
from md2blog.modules.identity.application.service.refresh import TokenPairResult
from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import DisplayName, Email, PasswordHash
from md2blog.modules.identity.presentation.dependencies import (
    get_login_use_case,
    get_refresh_service,
)
from md2blog.shared.domain.tsid import TSID


async def test_login_returns_access_token_and_sets_refresh_cookie() -> None:
    user = User(
        id=TSID(123456789),
        email=Email("user@example.com"),
        password_hash=PasswordHash("hidden"),
        display_name=DisplayName("User"),
    )
    login_use_case = AsyncMock()
    login_use_case.execute.return_value = LoginResult(user)
    refresh_service = AsyncMock()
    refresh_service.create.return_value = TokenPairResult(
        user,
        "access-token",
        "refresh-token",
    )
    app = create_app()
    app.dependency_overrides[get_login_use_case] = lambda: login_use_case
    app.dependency_overrides[get_refresh_service] = lambda: refresh_service
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            json={"email": "user@example.com", "password": "correct-password"},
        )

    assert response.status_code == 200
    assert response.json()["access_token"] == "access-token"
    assert "refresh_token=refresh-token" in response.headers["set-cookie"]
    assert "HttpOnly" in response.headers["set-cookie"]
