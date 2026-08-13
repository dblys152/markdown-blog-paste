from unittest.mock import AsyncMock

import httpx

from md2blog.main import create_app
from md2blog.modules.identity.application.service.login import LoginResult
from md2blog.modules.identity.application.service.refresh import TokenPairResult
from md2blog.modules.identity.domain.user import AuthenticationFailedError, User
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


async def test_login_returns_common_error_response_for_invalid_credentials() -> None:
    login_use_case = AsyncMock()
    login_use_case.execute.side_effect = AuthenticationFailedError
    app = create_app()
    app.dependency_overrides[get_login_use_case] = lambda: login_use_case
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            json={"email": "user@example.com", "password": "wrong-password"},
        )

    assert response.status_code == 401
    assert response.json() == {
        "code": "AUTH_INVALID_CREDENTIALS",
        "message": "이메일 또는 비밀번호가 올바르지 않습니다.",
    }


async def test_login_returns_field_errors_for_invalid_request() -> None:
    transport = httpx.ASGITransport(app=create_app())

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            json={"email": "not-an-email", "password": ""},
        )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert body["message"] == "입력값을 확인해주세요."
    assert {error["field"] for error in body["errors"]} == {"email", "password"}
