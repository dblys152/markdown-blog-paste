from datetime import UTC, datetime, timedelta

import pytest

from md2blog.modules.identity.domain.password_reset import (
    PasswordResetExpiredError,
    PasswordResetToken,
    PasswordResetUnavailableError,
)
from md2blog.shared.domain.tsid import TSID

NOW = datetime(2026, 9, 6, 12, tzinfo=UTC)


def make_token(*, expires_at: datetime | None = None) -> PasswordResetToken:
    return PasswordResetToken.issue(
        token_id=TSID(1),
        user_id=TSID(2),
        token_hash="hash",
        issued_at=NOW,
        expires_at=expires_at or NOW + timedelta(hours=1),
    )


def test_use_marks_password_reset_token_as_used() -> None:
    used = make_token().use(NOW + timedelta(minutes=1))

    assert used.used_at == NOW + timedelta(minutes=1)


def test_expired_password_reset_token_cannot_be_used() -> None:
    with pytest.raises(PasswordResetExpiredError):
        make_token(expires_at=NOW + timedelta(minutes=1)).use(NOW + timedelta(minutes=1))


def test_password_reset_token_can_only_be_used_once() -> None:
    token = make_token().use(NOW + timedelta(minutes=1))

    with pytest.raises(PasswordResetUnavailableError):
        token.use(NOW + timedelta(minutes=2))
