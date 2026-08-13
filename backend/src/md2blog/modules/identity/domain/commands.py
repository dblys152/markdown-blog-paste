from dataclasses import dataclass

from md2blog.modules.identity.domain.value_objects import (
    DisplayName,
    Email,
    PasswordHash,
    RawPassword,
)
from md2blog.shared.domain.tsid import TSID


@dataclass(frozen=True, slots=True)
class SignUpCommand:
    id: TSID
    email: Email
    password_hash: PasswordHash
    display_name: DisplayName


@dataclass(frozen=True, slots=True)
class LoginCommand:
    email: Email
    password: RawPassword
