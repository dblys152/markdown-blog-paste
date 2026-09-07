from datetime import UTC, datetime

from md2blog.modules.identity.application.models.google_auth import GoogleLoginStatus
from md2blog.modules.identity.application.port.outbound.google_identity import GoogleIdentityClaims
from md2blog.modules.identity.application.service.google_auth import (
    GetGoogleConnection,
    GoogleLogin,
)
from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.user_identity import IdentityProvider, UserIdentity
from md2blog.modules.identity.domain.value_objects import DisplayName, Email, PasswordHash
from md2blog.shared.domain.tsid import TSID


class Verifier:
    async def verify(self, credential: str) -> GoogleIdentityClaims:
        return GoogleIdentityClaims("google-sub", "user@example.com", True)


class Users:
    def __init__(self, user: User | None = None) -> None:
        self.user = user

    async def find_by_id(self, user_id: int) -> User | None:
        return self.user if self.user and self.user.id.value == user_id else None

    async def find_by_email(self, email: Email) -> User | None:
        return self.user if self.user and self.user.email == email else None


class Identities:
    def __init__(self, identity: UserIdentity | None = None) -> None:
        self.identity = identity

    async def find_by_provider_subject(
        self, provider: IdentityProvider, provider_subject: str
    ) -> UserIdentity | None:
        return self.identity

    async def find_by_user_and_provider(
        self, user_id: TSID, provider: IdentityProvider
    ) -> UserIdentity | None:
        if (
            self.identity
            and self.identity.user_id == user_id
            and self.identity.provider == provider
        ):
            return self.identity
        return None


def make_user() -> User:
    return User(
        id=TSID(1),
        email=Email("user@example.com"),
        password_hash=PasswordHash("hash"),
        display_name=DisplayName("사용자"),
    )


async def test_google_login_returns_link_required_for_existing_email() -> None:
    result = await GoogleLogin(Users(make_user()), Identities(), Verifier()).execute("token")

    assert result.status is GoogleLoginStatus.LINK_REQUIRED
    assert result.user is None


async def test_google_login_returns_signup_required_for_new_email() -> None:
    result = await GoogleLogin(Users(), Identities(), Verifier()).execute("token")

    assert result.status is GoogleLoginStatus.SIGNUP_REQUIRED


async def test_google_login_authenticates_linked_subject() -> None:
    user = make_user()
    identity = UserIdentity(
        id=TSID(2),
        user_id=user.id,
        provider=IdentityProvider.GOOGLE,
        provider_subject="google-sub",
        provider_email="user@example.com",
        created_at=datetime(2026, 9, 6, tzinfo=UTC),
    )

    result = await GoogleLogin(Users(user), Identities(identity), Verifier()).execute("token")

    assert result.status is GoogleLoginStatus.AUTHENTICATED
    assert result.user == user


async def test_google_connection_can_be_disconnected_when_password_login_remains() -> None:
    user = make_user()
    identity = UserIdentity(
        id=TSID(2),
        user_id=user.id,
        provider=IdentityProvider.GOOGLE,
        provider_subject="google-sub",
        provider_email="user@gmail.com",
        created_at=datetime(2026, 9, 6, tzinfo=UTC),
    )

    connection = await GetGoogleConnection(Identities(identity)).execute(user)

    assert connection.connected is True
    assert connection.can_disconnect is True


async def test_google_only_account_cannot_disconnect_last_sign_in_method() -> None:
    user = User(
        id=TSID(1),
        email=Email("user@example.com"),
        password_hash=None,
        display_name=DisplayName("사용자"),
    )
    identity = UserIdentity(
        id=TSID(2),
        user_id=user.id,
        provider=IdentityProvider.GOOGLE,
        provider_subject="google-sub",
        provider_email="user@gmail.com",
        created_at=datetime(2026, 9, 6, tzinfo=UTC),
    )

    connection = await GetGoogleConnection(Identities(identity)).execute(user)

    assert connection.connected is True
    assert connection.can_disconnect is False
