from dataclasses import dataclass

from md2blog.modules.identity.domain.user_identity import IdentityProvider
from md2blog.modules.identity.domain.value_objects import DisplayName, Email
from md2blog.shared.domain.events import DomainEvent
from md2blog.shared.domain.tsid import TSID


@dataclass(frozen=True, slots=True, kw_only=True)
class EmailVerificationRequested(DomainEvent):
    user_id: TSID
    email: Email
    display_name: DisplayName
    raw_token: str


@dataclass(frozen=True, slots=True, kw_only=True)
class PasswordResetRequested(DomainEvent):
    user_id: TSID
    email: Email
    display_name: DisplayName
    raw_token: str


@dataclass(frozen=True, slots=True, kw_only=True)
class AuthenticationSucceeded(DomainEvent):
    user_id: TSID


@dataclass(frozen=True, slots=True, kw_only=True)
class AuthenticationFailed(DomainEvent):
    user_id: TSID


@dataclass(frozen=True, slots=True, kw_only=True)
class EmailVerified(DomainEvent):
    user_id: TSID


@dataclass(frozen=True, slots=True, kw_only=True)
class PasswordResetCompleted(DomainEvent):
    user_id: TSID


@dataclass(frozen=True, slots=True, kw_only=True)
class AllSessionsRevoked(DomainEvent):
    user_id: TSID


@dataclass(frozen=True, slots=True, kw_only=True)
class UserIdentityLinked(DomainEvent):
    user_id: TSID
    provider: IdentityProvider


@dataclass(frozen=True, slots=True, kw_only=True)
class UserIdentityUnlinked(DomainEvent):
    user_id: TSID
    provider: IdentityProvider


@dataclass(frozen=True, slots=True, kw_only=True)
class AccountDeleted(DomainEvent):
    user_id: TSID
