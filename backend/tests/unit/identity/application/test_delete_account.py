from datetime import UTC, datetime

import pytest

from md2blog.modules.identity.application.service.delete_account import DeleteAccount
from md2blog.modules.identity.domain.commands import DeleteAccountCommand
from md2blog.modules.identity.domain.user import AccountDeletionPasswordMismatchError, User
from md2blog.modules.identity.domain.value_objects import (
    DisplayName,
    Email,
    PasswordHash,
    RawPassword,
)
from md2blog.shared.domain.tsid import TSID


class Users:
    def __init__(self) -> None:
        self.deleted_user: User | None = None

    async def delete(self, user: User) -> None:
        self.deleted_user = user


class Passwords:
    def __init__(self, matches: bool) -> None:
        self.matches = matches

    def verify(self, password: RawPassword, password_hash: PasswordHash) -> bool:
        return self.matches


def make_user() -> User:
    return User(
        id=TSID(1),
        email=Email("user@example.com"),
        password_hash=PasswordHash("hash"),
        display_name=DisplayName("User"),
        email_verified_at=datetime.now(UTC),
    )


async def test_delete_account_verifies_password_and_deletes_user() -> None:
    users = Users()
    service = DeleteAccount(users=users, password_hasher=Passwords(matches=True))  # type: ignore[arg-type]
    user = make_user()

    await service.execute(user, DeleteAccountCommand(password=RawPassword("password123")))

    assert users.deleted_user == user


async def test_delete_account_rejects_invalid_password() -> None:
    users = Users()
    service = DeleteAccount(users=users, password_hasher=Passwords(matches=False))  # type: ignore[arg-type]

    with pytest.raises(AccountDeletionPasswordMismatchError):
        await service.execute(
            make_user(),
            DeleteAccountCommand(password=RawPassword("password123")),
        )

    assert users.deleted_user is None
