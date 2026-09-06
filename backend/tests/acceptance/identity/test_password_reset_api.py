from unittest.mock import AsyncMock

import httpx

from md2blog.main import create_app
from md2blog.modules.identity.domain.commands import (
    ConfirmPasswordResetCommand,
    RequestPasswordResetCommand,
)
from md2blog.modules.identity.domain.value_objects import Email, RawPassword
from md2blog.modules.identity.presentation.dependencies import (
    get_confirm_password_reset,
    get_request_password_reset,
)


async def test_password_reset_request_returns_same_response() -> None:
    use_case = AsyncMock()
    app = create_app()
    app.dependency_overrides[get_request_password_reset] = lambda: use_case

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/auth/password-reset/request",
            json={"email": "user@example.com"},
        )

    assert response.status_code == 204
    use_case.execute.assert_awaited_once_with(
        RequestPasswordResetCommand(email=Email("user@example.com"))
    )


async def test_password_reset_confirm_changes_password_and_deletes_cookie() -> None:
    use_case = AsyncMock()
    app = create_app()
    app.dependency_overrides[get_confirm_password_reset] = lambda: use_case

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
        cookies={"refresh_token": "refresh-token"},
    ) as client:
        response = await client.post(
            "/auth/password-reset/confirm",
            json={"token": "raw-token", "new_password": "new-password"},
        )

    assert response.status_code == 204
    assert "refresh_token=" in response.headers["set-cookie"]
    assert "Max-Age=0" in response.headers["set-cookie"]
    use_case.execute.assert_awaited_once_with(
        ConfirmPasswordResetCommand(
            token="raw-token",
            new_password=RawPassword("new-password"),
        )
    )
