import pytest

from md2blog.modules.identity.domain.user import AuthenticationFailedError, User
from md2blog.modules.identity.domain.value_objects import DisplayName, Email, PasswordHash
from md2blog.shared.domain.tsid import TSID


def make_user(status: str = "active") -> User:
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
    [(False, "active"), (True, "suspended"), (True, "withdrawn")],
)
def test_authentication_fails_for_invalid_credentials_or_status(
    password_matches: bool,
    user_status: str,
) -> None:
    with pytest.raises(AuthenticationFailedError):
        make_user(user_status).authenticate(password_matches)
