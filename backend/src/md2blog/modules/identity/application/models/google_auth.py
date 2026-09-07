from dataclasses import dataclass
from enum import StrEnum

from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import Email


class GoogleLoginStatus(StrEnum):
    AUTHENTICATED = "authenticated"
    LINK_REQUIRED = "link_required"
    SIGNUP_REQUIRED = "signup_required"


@dataclass(frozen=True, slots=True)
class GoogleLoginResult:
    status: GoogleLoginStatus
    email: Email
    user: User | None = None


@dataclass(frozen=True, slots=True)
class GoogleConnection:
    connected: bool
    email: str | None = None
    can_disconnect: bool = False
