from dataclasses import dataclass
from datetime import datetime

from md2blog.modules.identity.domain.commands import SignUpCommand
from md2blog.modules.identity.domain.value_objects import DisplayName, Email, PasswordHash
from md2blog.shared.domain.tsid import TSID


@dataclass(frozen=True, slots=True)
class User:
    id: TSID
    email: Email
    password_hash: PasswordHash
    display_name: DisplayName
    email_verified_at: datetime | None = None
    status: str = "active"

    @classmethod
    def sign_up(cls, command: SignUpCommand) -> "User":
        return cls(
            id=command.id,
            email=command.email,
            password_hash=command.password_hash,
            display_name=command.display_name,
        )

    def authenticate(self, password_matches: bool) -> None:
        if not password_matches or self.status != "active":
            raise AuthenticationFailedError


class AuthenticationFailedError(Exception):
    pass
