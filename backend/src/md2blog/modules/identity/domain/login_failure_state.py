from dataclasses import dataclass
from datetime import datetime, timedelta

from md2blog.shared.domain.tsid import TSID


@dataclass(frozen=True, slots=True)
class LoginFailurePolicy:
    failure_limit: int = 10
    window: timedelta = timedelta(minutes=10)
    block_duration: timedelta = timedelta(minutes=5)


@dataclass(slots=True)
class LoginFailureState:
    user_id: TSID
    failure_count: int
    window_started_at: datetime
    blocked_until: datetime | None = None

    @classmethod
    def first_failure(cls, user_id: TSID, now: datetime) -> "LoginFailureState":
        return cls(user_id, 1, now)

    def retry_after_seconds(self, now: datetime) -> int:
        if self.blocked_until is None or self.blocked_until <= now:
            return 0
        return max(1, int((self.blocked_until - now).total_seconds()))

    def record_failure(self, now: datetime, policy: LoginFailurePolicy) -> None:
        if self.retry_after_seconds(now) > 0:
            return
        if self.blocked_until is not None or now >= self.window_started_at + policy.window:
            self.failure_count = 1
            self.window_started_at = now
            self.blocked_until = None
            return

        self.failure_count += 1
        if self.failure_count >= policy.failure_limit:
            self.blocked_until = now + policy.block_duration


class LoginRateLimitedError(Exception):
    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__("login attempts are rate limited")
