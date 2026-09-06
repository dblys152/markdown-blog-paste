from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from md2blog.modules.identity.domain.commands import SignUpCommand
from md2blog.modules.identity.domain.value_objects import DisplayName, Email, PasswordHash
from md2blog.shared.domain.tsid import TSID


class UserStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    WITHDRAWN = "withdrawn"


@dataclass(frozen=True, slots=True)
class User:
    id: TSID
    email: Email
    password_hash: PasswordHash
    display_name: DisplayName
    email_verified_at: datetime | None = None
    status: UserStatus = UserStatus.ACTIVE

    @classmethod
    def sign_up(cls, command: SignUpCommand) -> "User":
        return cls(
            id=command.id,
            email=command.email,
            password_hash=command.password_hash,
            display_name=command.display_name,
        )

    def authenticate(self, password_matches: bool) -> None:
        if not password_matches or self.status is not UserStatus.ACTIVE:
            raise AuthenticationFailedError

    def confirm_account_deletion(self, password_matches: bool) -> None:
        if not password_matches:
            raise AccountDeletionPasswordMismatchError
        self.ensure_access_allowed()

    def ensure_access_allowed(self) -> None:
        if self.status is not UserStatus.ACTIVE:
            raise AccessNotAllowedError

    def ensure_email_verified(self) -> None:
        if not self.is_email_verified:
            raise EmailVerificationRequiredError

    def verify_email(self, verified_at: datetime) -> "User":
        if self.email_verified_at is not None:
            return self
        return replace(self, email_verified_at=verified_at)

    def reset_password(self, password_hash: PasswordHash) -> "User":
        self.ensure_access_allowed()
        return replace(self, password_hash=password_hash)

    @property
    def is_email_verified(self) -> bool:
        return self.email_verified_at is not None


class AuthenticationFailedError(Exception):
    pass


class AccessNotAllowedError(Exception):
    pass


class EmailVerificationRequiredError(Exception):
    pass


class AccountDeletionPasswordMismatchError(Exception):
    pass
