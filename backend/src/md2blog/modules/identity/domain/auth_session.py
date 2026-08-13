from dataclasses import dataclass, replace
from datetime import datetime

from md2blog.shared.domain.tsid import TSID


@dataclass(frozen=True, slots=True)
class AuthSession:
    id: TSID
    user_id: TSID
    refresh_token_hash: str
    expires_at: datetime
    created_at: datetime
    revoked_at: datetime | None = None
    replaced_by_token_hash: str | None = None
    user_agent: str | None = None
    ip_address: str | None = None

    def is_active(self, now: datetime) -> bool:
        return self.revoked_at is None and self.expires_at > now

    def rotate(self, *, now: datetime, replacement_hash: str) -> "AuthSession":
        if not self.is_active(now):
            raise InvalidRefreshSessionError
        return replace(
            self,
            revoked_at=now,
            replaced_by_token_hash=replacement_hash,
        )

    def revoke(self, now: datetime) -> "AuthSession":
        if self.revoked_at is not None:
            return self
        return replace(self, revoked_at=now)


class InvalidRefreshSessionError(Exception):
    pass


class RefreshTokenReuseDetectedError(Exception):
    pass
