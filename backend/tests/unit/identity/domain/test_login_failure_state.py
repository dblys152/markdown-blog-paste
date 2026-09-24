from datetime import UTC, datetime, timedelta

from md2blog.modules.identity.domain.login_failure_state import (
    LoginFailurePolicy,
    LoginFailureState,
)
from md2blog.shared.domain.tsid import TSID

NOW = datetime(2026, 9, 14, tzinfo=UTC)
POLICY = LoginFailurePolicy()


def test_user_is_blocked_on_tenth_failure() -> None:
    state = LoginFailureState(TSID(1), 9, NOW)

    state.record_failure(NOW + timedelta(minutes=1), POLICY)

    assert state.failure_count == 10
    assert state.retry_after_seconds(NOW + timedelta(minutes=1)) == 300


def test_expired_window_starts_again_from_first_failure() -> None:
    state = LoginFailureState(TSID(1), 9, NOW)

    state.record_failure(NOW + timedelta(minutes=10), POLICY)

    assert state.failure_count == 1
    assert state.window_started_at == NOW + timedelta(minutes=10)
    assert state.blocked_until is None


def test_expired_block_is_automatically_released_with_a_new_window() -> None:
    state = LoginFailureState(
        TSID(1),
        10,
        NOW,
        blocked_until=NOW + timedelta(minutes=5),
    )

    state.record_failure(NOW + timedelta(minutes=5), POLICY)

    assert state.failure_count == 1
    assert state.blocked_until is None
