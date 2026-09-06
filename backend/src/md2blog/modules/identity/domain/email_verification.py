from dataclasses import dataclass, replace
from datetime import datetime

from md2blog.shared.domain.tsid import TSID


@dataclass(frozen=True, slots=True, kw_only=True)
class EmailVerificationToken:
    id: TSID
    user_id: TSID
    token_hash: str
    expires_at: datetime
    created_at: datetime
    used_at: datetime | None = None
    revoked_at: datetime | None = None

    @classmethod
    def issue(
        cls,
        *,
        token_id: TSID,
        user_id: TSID,
        token_hash: str,
        issued_at: datetime,
        expires_at: datetime,
    ) -> "EmailVerificationToken":
        if not token_hash:
            raise ValueError("token hash must not be empty")
        if expires_at <= issued_at:
            raise ValueError("expiration must be later than issuance")
        return cls(
            id=token_id,
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            created_at=issued_at,
        )

    def confirm(self, confirmed_at: datetime) -> "EmailVerificationToken":
        if self.used_at is not None or self.revoked_at is not None:
            raise EmailVerificationUnavailableError
        if confirmed_at >= self.expires_at:
            raise EmailVerificationExpiredError
        return replace(self, used_at=confirmed_at)

    def revoke(self, revoked_at: datetime) -> "EmailVerificationToken":
        if self.used_at is not None or self.revoked_at is not None:
            return self
        return replace(self, revoked_at=revoked_at)

    def is_active(self, now: datetime) -> bool:
        return self.used_at is None and self.revoked_at is None and now < self.expires_at


class EmailVerificationError(Exception):
    pass


class EmailVerificationExpiredError(EmailVerificationError):
    pass


class EmailVerificationUnavailableError(EmailVerificationError):
    pass
