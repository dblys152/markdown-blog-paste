from datetime import UTC, datetime

import pytest

from md2blog.modules.identity.domain.user import (
    AuthenticationFailedError,
    EmailVerificationRequiredError,
    User,
    UserStatus,
)
from md2blog.modules.identity.domain.value_objects import DisplayName, Email, PasswordHash
from md2blog.shared.domain.tsid import TSID


def make_user(status: UserStatus = UserStatus.ACTIVE) -> User:
    return User(
        id=TSID(1),
        email=Email("user@example.com"),
        password_hash=PasswordHash("hash"),
        display_name=DisplayName("User"),
        status=status,
    )


def test_active_user_authenticates_with_matching_password() -> None:
    make_user().authenticate(password_matches=True)


@pytest.mark.parametrize(
    ("password_matches", "user_status"),
    [
        (False, UserStatus.ACTIVE),
        (True, UserStatus.SUSPENDED),
        (True, UserStatus.WITHDRAWN),
    ],
)
def test_authentication_fails_for_invalid_credentials_or_status(
    password_matches: bool,
    user_status: UserStatus,
) -> None:
    with pytest.raises(AuthenticationFailedError):
        make_user(user_status).authenticate(password_matches)


def test_user_verifies_email_once() -> None:
    verified_at = datetime(2026, 8, 26, tzinfo=UTC)

    verified_user = make_user().verify_email(verified_at)

    assert verified_user.email_verified_at == verified_at
    assert verified_user.is_email_verified
    assert verified_user.verify_email(datetime(2026, 8, 27, tzinfo=UTC)) == verified_user


def test_unverified_user_cannot_access_workspace() -> None:
    with pytest.raises(EmailVerificationRequiredError):
        make_user().ensure_email_verified()
