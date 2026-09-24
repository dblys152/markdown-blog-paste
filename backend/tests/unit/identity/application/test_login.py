from datetime import UTC, datetime

import pytest

from md2blog.modules.identity.application.service.login import Login
from md2blog.modules.identity.domain.commands import LoginCommand
from md2blog.modules.identity.domain.login_failure_state import (
    LoginFailurePolicy,
    LoginFailureState,
    LoginRateLimitedError,
)
from md2blog.modules.identity.domain.user import AuthenticationFailedError, User, UserStatus
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


class Failures:
    def __init__(self) -> None:
        self.items: dict[TSID, LoginFailureState] = {}

    async def find_for_update(self, user_id: TSID) -> LoginFailureState | None:
        return self.items.get(user_id)

    async def add(self, state: LoginFailureState) -> None:
        self.items[state.user_id] = state

    async def save(self, state: LoginFailureState) -> None:
        self.items[state.user_id] = state

    async def delete(self, user_id: TSID) -> None:
        self.items.pop(user_id, None)


class Clock:
    now_value = datetime(2026, 9, 14, tzinfo=UTC)

    def now(self) -> datetime:
        return self.now_value


def make_service(user: User | None, failures: Failures | None = None) -> Login:
    return Login(
        Users(user),
        Passwords(),
        failures if failures is not None else Failures(),
        Clock(),
        LoginFailurePolicy(),
    )


def make_user(status: UserStatus = UserStatus.ACTIVE) -> User:
    return User(
        id=TSID(1),
        email=Email("user@example.com"),
        password_hash=PasswordHash("hash:correct-password"),
        display_name=DisplayName("User"),
        status=status,
    )


async def test_login_returns_active_user_for_valid_credentials() -> None:
    service = make_service(make_user())

    result = await service.execute(
        LoginCommand(Email("user@example.com"), RawPassword("correct-password"))
    )

    assert result.user == make_user()


@pytest.mark.parametrize(
    ("user", "password"),
    [
        (None, "correct-password"),
        (make_user(), "wrong-password"),
        (make_user(UserStatus.SUSPENDED), "correct-password"),
    ],
)
async def test_login_rejects_unknown_user_wrong_password_and_inactive_user(
    user: User | None,
    password: str,
) -> None:
    service = make_service(user)

    with pytest.raises(AuthenticationFailedError):
        await service.execute(LoginCommand(Email("user@example.com"), RawPassword(password)))


async def test_tenth_email_failure_blocks_login_for_five_minutes() -> None:
    failures = Failures()
    service = make_service(make_user(), failures)
    command = LoginCommand(Email("user@example.com"), RawPassword("wrong-password"))

    for _ in range(9):
        with pytest.raises(AuthenticationFailedError):
            await service.execute(command)

    with pytest.raises(LoginRateLimitedError) as raised:
        await service.execute(command)

    assert raised.value.retry_after_seconds == 300


async def test_successful_login_clears_email_failures() -> None:
    failures = Failures()
    failures.items[TSID(1)] = LoginFailureState(TSID(1), 3, Clock.now_value)
    service = make_service(make_user(), failures)

    await service.execute(LoginCommand(Email("user@example.com"), RawPassword("correct-password")))

    assert TSID(1) not in failures.items


async def test_unknown_email_does_not_create_failure_state() -> None:
    failures = Failures()
    service = make_service(None, failures)

    with pytest.raises(AuthenticationFailedError):
        await service.execute(LoginCommand(Email("unknown@example.com"), RawPassword("wrong")))

    assert failures.items == {}
