from datetime import UTC, datetime, timedelta

import pytest

from md2blog.modules.identity.domain.auth_session import (
    AuthSession,
    InvalidRefreshSessionError,
)
from md2blog.shared.domain.tsid import TSID


def test_active_session_can_be_rotated() -> None:
    now = datetime.now(UTC)
    session = AuthSession(
        id=TSID(1),
        user_id=TSID(2),
        refresh_token_hash="old",
        expires_at=now + timedelta(days=1),
        created_at=now,
    )

    rotated = session.rotate(now=now, replacement_hash="new")

    assert rotated.revoked_at == now
    assert rotated.replaced_by_token_hash == "new"
    assert not rotated.is_active(now)


def test_expired_session_cannot_be_rotated() -> None:
    now = datetime.now(UTC)
    session = AuthSession(
        id=TSID(1),
        user_id=TSID(2),
        refresh_token_hash="old",
        expires_at=now,
        created_at=now - timedelta(days=1),
    )

    with pytest.raises(InvalidRefreshSessionError):
        session.rotate(now=now, replacement_hash="new")


def test_session_revocation_is_idempotent() -> None:
    now = datetime.now(UTC)
    session = AuthSession(
        id=TSID(1),
        user_id=TSID(2),
        refresh_token_hash="token",
        expires_at=now + timedelta(days=1),
        created_at=now,
    )

    revoked = session.revoke(now)

    assert revoked.revoked_at == now
    assert revoked.revoke(now + timedelta(hours=1)) == revoked
