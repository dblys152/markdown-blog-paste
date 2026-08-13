import pytest

from md2blog.modules.identity.application.service.login import Login
from md2blog.modules.identity.domain.commands import LoginCommand
from md2blog.modules.identity.domain.user import AuthenticationFailedError, User
from md2blog.modules.identity.domain.value_objects import (
    DisplayName,
    Email,
    PasswordHash,
    RawPassword,
)
from md2blog.shared.domain.tsid import TSID


class Users:
    def __init__(self, user: User | None) -> None:
        self.user = user

    async def exists_by_email(self, email: Email) -> bool:
        return self.user is not None and self.user.email == email

    async def add(self, user: User) -> None:
        self.user = user

    async def find_by_id(self, user_id: int) -> User | None:
        return self.user if self.user and self.user.id.value == user_id else None

    async def find_by_email(self, email: Email) -> User | None:
        return self.user if self.user and self.user.email == email else None


class Passwords:
    def hash(self, password: RawPassword) -> PasswordHash:
        return PasswordHash(f"hash:{password.value}")

    def verify(self, password: RawPassword, password_hash: PasswordHash) -> bool:
        return password_hash.value == f"hash:{password.value}"


def make_user(status: str = "active") -> User:
    return User(
        id=TSID(1),
        email=Email("user@example.com"),
        password_hash=PasswordHash("hash:correct-password"),
        display_name=DisplayName("User"),
        status=status,
    )


async def test_login_returns_active_user_for_valid_credentials() -> None:
    service = Login(Users(make_user()), Passwords())

    result = await service.execute(
        LoginCommand(Email("user@example.com"), RawPassword("correct-password"))
    )

    assert result.user == make_user()


@pytest.mark.parametrize(
    ("user", "password"),
    [
        (None, "correct-password"),
        (make_user(), "wrong-password"),
        (make_user("suspended"), "correct-password"),
    ],
)
async def test_login_rejects_unknown_user_wrong_password_and_inactive_user(
    user: User | None,
    password: str,
) -> None:
    service = Login(Users(user), Passwords())

    with pytest.raises(AuthenticationFailedError):
        await service.execute(LoginCommand(Email("user@example.com"), RawPassword(password)))
