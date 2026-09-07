from datetime import UTC, datetime

import pytest

from md2blog.modules.identity.application.port.outbound.google_identity import GoogleIdentityClaims
from md2blog.modules.identity.application.service.delete_account import DeleteAccount
from md2blog.modules.identity.domain.commands import DeleteAccountCommand
from md2blog.modules.identity.domain.user import AccountDeletionPasswordMismatchError, User
from md2blog.modules.identity.domain.user_identity import IdentityProvider, UserIdentity
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


class Identities:
    def __init__(self, identity: UserIdentity | None = None) -> None:
        self.identity = identity

    async def find_by_user_and_provider(
        self, user_id: TSID, provider: IdentityProvider
    ) -> UserIdentity | None:
        return self.identity


class GoogleVerifier:
    async def verify(self, credential: str) -> GoogleIdentityClaims:
        return GoogleIdentityClaims("google-sub", "user@example.com", True)


def make_service(
    users: Users,
    passwords: Passwords,
    identity: UserIdentity | None = None,
) -> DeleteAccount:
    return DeleteAccount(
        users=users,  # type: ignore[arg-type]
        password_hasher=passwords,  # type: ignore[arg-type]
        identities=Identities(identity),  # type: ignore[arg-type]
        google_verifier=GoogleVerifier(),
    )


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
    service = make_service(users, Passwords(matches=True))
    user = make_user()

    await service.execute(user, DeleteAccountCommand(password=RawPassword("password123")))

    assert users.deleted_user == user


async def test_delete_account_rejects_invalid_password() -> None:
    users = Users()
    service = make_service(users, Passwords(matches=False))

    with pytest.raises(AccountDeletionPasswordMismatchError):
        await service.execute(
            make_user(),
            DeleteAccountCommand(password=RawPassword("password123")),
        )

    assert users.deleted_user is None


async def test_google_only_account_is_deleted_after_google_reauthentication() -> None:
    users = Users()
    user = User(
        id=TSID(1),
        email=Email("user@example.com"),
        password_hash=None,
        display_name=DisplayName("User"),
        email_verified_at=datetime.now(UTC),
    )
    identity = UserIdentity(
        id=TSID(2),
        user_id=user.id,
        provider=IdentityProvider.GOOGLE,
        provider_subject="google-sub",
        provider_email="user@example.com",
        created_at=datetime.now(UTC),
    )

    await make_service(users, Passwords(matches=False), identity).execute(
        user,
        DeleteAccountCommand(google_credential="credential"),
    )

    assert users.deleted_user == user
