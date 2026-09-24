from datetime import UTC, datetime, timedelta

import pytest

from md2blog.modules.identity.domain.account_confirmation_token import (
    AccountConfirmationToken,
    AccountConfirmationTokenExpiredError,
    AccountConfirmationTokenPurpose,
    AccountConfirmationTokenUnavailableError,
)
from md2blog.shared.domain.tsid import TSID

NOW = datetime(2026, 9, 6, 12, tzinfo=UTC)


def make_token(
    purpose: AccountConfirmationTokenPurpose = AccountConfirmationTokenPurpose.EMAIL_VERIFICATION,
) -> AccountConfirmationToken:
    return AccountConfirmationToken.issue(
        token_id=TSID(1),
        user_id=TSID(2),
        purpose=purpose,
        token_hash="hash",
        issued_at=NOW,
        expires_at=NOW + timedelta(hours=1),
    )


@pytest.mark.parametrize("purpose", list(AccountConfirmationTokenPurpose))
def test_token_can_be_used_once_for_each_purpose(purpose: AccountConfirmationTokenPurpose) -> None:
    used = make_token(purpose).use(NOW + timedelta(minutes=1))

    assert used.purpose == purpose
    assert used.used_at == NOW + timedelta(minutes=1)
    assert not used.is_active(NOW + timedelta(minutes=2))
    with pytest.raises(AccountConfirmationTokenUnavailableError):
        used.use(NOW + timedelta(minutes=2))


def test_expired_or_revoked_token_cannot_be_used() -> None:
    with pytest.raises(AccountConfirmationTokenExpiredError):
        make_token().use(NOW + timedelta(hours=1))
    with pytest.raises(AccountConfirmationTokenUnavailableError):
        make_token().revoke(NOW).use(NOW + timedelta(minutes=1))
