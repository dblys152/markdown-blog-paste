from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


@dataclass(frozen=True, slots=True)
class GoogleIdentityClaims:
    subject: str
    email: str
    email_verified: bool


class GoogleCredentialFailureReason(StrEnum):
    AUDIENCE_MISMATCH = "audience_mismatch"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_NOT_YET_VALID = "token_not_yet_valid"
    INVALID_ISSUER = "invalid_issuer"
    CERTIFICATE_FETCH_FAILED = "certificate_fetch_failed"
    SIGNATURE_VERIFICATION_FAILED = "signature_verification_failed"
    EMAIL_NOT_VERIFIED = "email_not_verified"
    CREDENTIAL_MISSING = "credential_missing"
    INVALID_CLAIMS = "invalid_claims"
    IDENTITY_MISMATCH = "identity_mismatch"
    INVALID_TOKEN = "invalid_token"


class InvalidGoogleCredentialError(Exception):
    def __init__(self, reason: GoogleCredentialFailureReason) -> None:
        self.reason = reason
        super().__init__(reason.value)


class GoogleIdentityVerifier(Protocol):
    async def verify(self, credential: str) -> GoogleIdentityClaims: ...
