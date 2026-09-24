from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from md2blog.shared.domain.tsid import TSID


class AccountConfirmationTokenPurpose(StrEnum):
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"


@dataclass(frozen=True, slots=True, kw_only=True)
class AccountConfirmationToken:
    id: TSID
    user_id: TSID
    purpose: AccountConfirmationTokenPurpose
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
        purpose: AccountConfirmationTokenPurpose,
        token_hash: str,
        issued_at: datetime,
        expires_at: datetime,
    ) -> "AccountConfirmationToken":
        if not token_hash:
            raise ValueError("token hash must not be empty")
        if expires_at <= issued_at:
            raise ValueError("expiration must be later than issuance")
        return cls(
            id=token_id,
            user_id=user_id,
            purpose=purpose,
            token_hash=token_hash,
            expires_at=expires_at,
            created_at=issued_at,
        )

    def use(self, used_at: datetime) -> "AccountConfirmationToken":
        if self.used_at is not None or self.revoked_at is not None:
            raise AccountConfirmationTokenUnavailableError
        if used_at >= self.expires_at:
            raise AccountConfirmationTokenExpiredError
        return replace(self, used_at=used_at)

    def revoke(self, revoked_at: datetime) -> "AccountConfirmationToken":
        if self.used_at is not None or self.revoked_at is not None:
            return self
        return replace(self, revoked_at=revoked_at)

    def is_active(self, now: datetime) -> bool:
        return self.used_at is None and self.revoked_at is None and now < self.expires_at


class AccountConfirmationTokenExpiredError(Exception):
    pass


class AccountConfirmationTokenUnavailableError(Exception):
    pass
