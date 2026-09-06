from datetime import UTC, datetime
from unittest.mock import AsyncMock

import httpx

from md2blog.main import create_app
from md2blog.modules.identity.application.service.email_verification import (
    EmailVerificationCooldownError,
    InvalidEmailVerificationTokenError,
)
from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import DisplayName, Email, PasswordHash
from md2blog.modules.identity.presentation.dependencies import (
    get_confirm_email_verification,
    get_current_user,
    get_issue_email_verification,
)
from md2blog.shared.domain.tsid import TSID


def make_user(*, verified: bool = False) -> User:
    return User(
        id=TSID(123456789),
        email=Email("user@example.com"),
        password_hash=PasswordHash("hidden"),
        display_name=DisplayName("User"),
        email_verified_at=datetime(2026, 8, 27, tzinfo=UTC) if verified else None,
    )


async def test_authenticated_user_can_request_verification_email() -> None:
    use_case = AsyncMock()
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: make_user()
    app.dependency_overrides[get_issue_email_verification] = lambda: use_case

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/auth/email-verification/request")

    assert response.status_code == 204
    use_case.execute.assert_awaited_once()


async def test_verification_token_can_be_confirmed_without_login() -> None:
    use_case = AsyncMock()
    use_case.execute.return_value = make_user(verified=True)
    app = create_app()
    app.dependency_overrides[get_confirm_email_verification] = lambda: use_case

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/auth/email-verification/confirm",
            json={"token": "raw-token"},
        )

    assert response.status_code == 200
    assert response.json()["email_verified"] is True
    use_case.execute.assert_awaited_once_with("raw-token")


async def test_invalid_verification_token_returns_common_error() -> None:
    use_case = AsyncMock()
    use_case.execute.side_effect = InvalidEmailVerificationTokenError
    app = create_app()
    app.dependency_overrides[get_confirm_email_verification] = lambda: use_case

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/auth/email-verification/confirm",
            json={"token": "invalid-token"},
        )

    assert response.status_code == 400
    assert response.json()["code"] == "AUTH_EMAIL_VERIFICATION_INVALID"


async def test_resend_cooldown_returns_retry_after_header() -> None:
    use_case = AsyncMock()
    use_case.execute.side_effect = EmailVerificationCooldownError(30)
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: make_user()
    app.dependency_overrides[get_issue_email_verification] = lambda: use_case

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/auth/email-verification/request")

    assert response.status_code == 429
    assert response.headers["retry-after"] == "30"
