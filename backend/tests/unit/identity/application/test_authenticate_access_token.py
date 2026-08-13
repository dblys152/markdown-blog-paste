import pytest

from md2blog.modules.identity.application.service.authenticate_access_token import (
    AuthenticateAccessToken,
    AuthenticationRequiredError,
)
from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import DisplayName, Email, PasswordHash
from md2blog.shared.domain.tsid import TSID


class Decoder:
    def decode_subject(self, token: str) -> TSID:
        return TSID.from_string(token)


class Users:
    def __init__(self, user: User | None) -> None:
        self.user = user

    async def find_by_id(self, user_id: int) -> User | None:
        return self.user if self.user and self.user.id.value == user_id else None


def make_user(status: str = "active") -> User:
    return User(
        id=TSID(123),
        email=Email("user@example.com"),
        password_hash=PasswordHash("hash"),
        display_name=DisplayName("User"),
        status=status,
    )


async def test_authenticate_access_token_returns_active_user() -> None:
    user = make_user()
    service = AuthenticateAccessToken(Decoder(), Users(user))

    assert await service.execute("123") == user


@pytest.mark.parametrize("user", [None, make_user("suspended")])
async def test_authenticate_access_token_rejects_missing_or_inactive_user(
    user: User | None,
) -> None:
    service = AuthenticateAccessToken(Decoder(), Users(user))

    with pytest.raises(AuthenticationRequiredError):
        await service.execute("123")
