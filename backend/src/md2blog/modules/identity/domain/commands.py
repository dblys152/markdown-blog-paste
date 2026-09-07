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


@dataclass(frozen=True, slots=True)
class DeleteAccountCommand:
    password: RawPassword | None = None
    google_credential: str | None = None


@dataclass(frozen=True, slots=True)
class UpdateDisplayNameCommand:
    display_name: DisplayName


@dataclass(frozen=True, slots=True)
class RequestPasswordResetCommand:
    email: Email


@dataclass(frozen=True, slots=True)
class ConfirmPasswordResetCommand:
    token: str
    new_password: RawPassword


@dataclass(frozen=True, slots=True)
class GoogleSignUpCommand:
    credential: str
    display_name: DisplayName


@dataclass(frozen=True, slots=True)
class LinkGoogleAndLoginCommand:
    credential: str
    password: RawPassword
