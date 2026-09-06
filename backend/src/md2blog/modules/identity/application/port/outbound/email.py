from dataclasses import dataclass
from typing import Protocol

from md2blog.modules.identity.domain.value_objects import Email


@dataclass(frozen=True, slots=True)
class OutboundEmail:
    to: Email
    subject: str
    html: str


class EmailSender(Protocol):
    async def send(self, message: OutboundEmail) -> None: ...


class EmailDeliveryError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class GeneratedEmailVerificationToken:
    raw: str
    token_hash: str


class EmailVerificationTokenManager(Protocol):
    def generate(self) -> GeneratedEmailVerificationToken: ...

    def hash(self, raw_token: str) -> str: ...
