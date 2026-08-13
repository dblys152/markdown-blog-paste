from dataclasses import dataclass
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

    def ensure_access_allowed(self) -> None:
        if self.status is not UserStatus.ACTIVE:
            raise AccessNotAllowedError


class AuthenticationFailedError(Exception):
    pass


class AccessNotAllowedError(Exception):
    pass
