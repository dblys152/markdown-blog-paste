from unittest.mock import AsyncMock

import httpx

from md2blog.main import create_app
from md2blog.modules.identity.application.service.signup import SignUpResult
from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import DisplayName, Email, PasswordHash
from md2blog.modules.identity.presentation.router import get_signup_dependencies
from md2blog.shared.domain.tsid import TSID


async def test_signup_returns_access_token_and_string_user_id() -> None:
    use_case = AsyncMock()
    use_case.execute.return_value = SignUpResult(
        user=User(
            id=TSID(123456789),
            email=Email("user@example.com"),
            password_hash=PasswordHash("hidden"),
            display_name=DisplayName("User"),
        ),
        access_token="access-token",
    )
    app = create_app()
    command_factory = AsyncMock()
    app.dependency_overrides[get_signup_dependencies] = lambda: (command_factory, use_case)
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/auth/signup",
            json={
                "email": "user@example.com",
                "password": "strong-password",
                "display_name": "User",
            },
        )

    assert response.status_code == 201
    assert response.json() == {
        "access_token": "access-token",
        "token_type": "bearer",
        "user": {
            "id": "123456789",
            "email": "user@example.com",
            "display_name": "User",
        },
    }
