from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import PasswordHash, RawPassword


class PasswordHasher(Protocol):
    def hash(self, password: RawPassword) -> PasswordHash: ...


class AccessTokenIssuer(Protocol):
    def issue(self, user: User) -> str: ...


@dataclass(frozen=True, slots=True)
class RefreshToken:
    raw: str
    token_hash: str


class RefreshTokenManager(Protocol):
    def generate(self) -> RefreshToken: ...

    def hash(self, raw_token: str) -> str: ...


class Clock(Protocol):
    def now(self) -> datetime: ...
