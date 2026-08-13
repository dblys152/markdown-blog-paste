from unittest.mock import AsyncMock

import httpx

from md2blog.main import create_app
from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import DisplayName, Email, PasswordHash
from md2blog.modules.identity.presentation.dependencies import get_authenticate_access_token
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
    }


async def test_me_requires_bearer_token() -> None:
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/auth/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
