from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class GoogleIdentityClaims:
    subject: str
    email: str
    email_verified: bool


class InvalidGoogleCredentialError(Exception):
    pass


class GoogleIdentityVerifier(Protocol):
    async def verify(self, credential: str) -> GoogleIdentityClaims: ...
