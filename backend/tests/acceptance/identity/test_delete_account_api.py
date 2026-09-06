from datetime import UTC, datetime
from unittest.mock import AsyncMock

import httpx

from md2blog.main import create_app
from md2blog.modules.identity.domain.commands import DeleteAccountCommand
from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import (
    DisplayName,
    Email,
    PasswordHash,
    RawPassword,
)
from md2blog.modules.identity.presentation.dependencies import (
    get_current_user,
    get_delete_account,
)
from md2blog.shared.domain.tsid import TSID


async def test_delete_account_deletes_user_and_refresh_cookie() -> None:
    user = User(
        id=TSID(1),
        email=Email("user@example.com"),
        password_hash=PasswordHash("hash"),
        display_name=DisplayName("User"),
        email_verified_at=datetime.now(UTC),
    )
    use_case = AsyncMock()
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_delete_account] = lambda: use_case

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
        cookies={"refresh_token": "refresh-token"},
    ) as client:
        response = await client.request(
            "DELETE",
            "/auth/account",
            json={"password": "password123"},
            headers={"Authorization": "Bearer access-token"},
        )

    assert response.status_code == 204
    assert response.content == b""
    assert "refresh_token=" in response.headers["set-cookie"]
    assert "Max-Age=0" in response.headers["set-cookie"]
    use_case.execute.assert_awaited_once_with(
        user,
        DeleteAccountCommand(password=RawPassword("password123")),
    )
