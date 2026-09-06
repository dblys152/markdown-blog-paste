from datetime import UTC, datetime, timedelta

import pytest

from md2blog.modules.identity.domain.email_verification import (
    EmailVerificationExpiredError,
    EmailVerificationToken,
    EmailVerificationUnavailableError,
)
from md2blog.shared.domain.tsid import TSID

NOW = datetime(2026, 8, 26, 12, tzinfo=UTC)


def make_token() -> EmailVerificationToken:
    return EmailVerificationToken.issue(
        token_id=TSID(10),
        user_id=TSID(1),
        token_hash="token-hash",
        issued_at=NOW,
        expires_at=NOW + timedelta(hours=24),
    )


def test_active_token_can_be_confirmed() -> None:
    confirmed = make_token().confirm(NOW + timedelta(minutes=1))

    assert confirmed.used_at == NOW + timedelta(minutes=1)
    assert not confirmed.is_active(NOW + timedelta(minutes=2))


def test_expired_token_cannot_be_confirmed() -> None:
    with pytest.raises(EmailVerificationExpiredError):
        make_token().confirm(NOW + timedelta(hours=24))


def test_used_or_revoked_token_cannot_be_confirmed() -> None:
    used = make_token().confirm(NOW + timedelta(minutes=1))
    revoked = make_token().revoke(NOW + timedelta(minutes=1))

    with pytest.raises(EmailVerificationUnavailableError):
        used.confirm(NOW + timedelta(minutes=2))
    with pytest.raises(EmailVerificationUnavailableError):
        revoked.confirm(NOW + timedelta(minutes=2))
