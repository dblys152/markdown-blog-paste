import asyncio

from google.auth.exceptions import GoogleAuthError, TransportError
from google.auth.transport.requests import Request
from google.oauth2 import id_token

from md2blog.modules.identity.application.port.outbound.google_identity import (
    GoogleCredentialFailureReason,
    GoogleIdentityClaims,
    InvalidGoogleCredentialError,
)


def classify_verification_failure(error: Exception) -> GoogleCredentialFailureReason:
    if isinstance(error, TransportError):
        return GoogleCredentialFailureReason.CERTIFICATE_FETCH_FAILED

    message = str(error).lower()
    if "audience" in message:
        return GoogleCredentialFailureReason.AUDIENCE_MISMATCH
    if "expired" in message:
        return GoogleCredentialFailureReason.TOKEN_EXPIRED
    if "too early" in message or "clock" in message:
        return GoogleCredentialFailureReason.TOKEN_NOT_YET_VALID
    if "issuer" in message:
        return GoogleCredentialFailureReason.INVALID_ISSUER
    if "signature" in message:
        return GoogleCredentialFailureReason.SIGNATURE_VERIFICATION_FAILED
    return GoogleCredentialFailureReason.INVALID_TOKEN


class GoogleIdTokenVerifier:
    def __init__(self, client_id: str) -> None:
        self._client_id = client_id

    async def verify(self, credential: str) -> GoogleIdentityClaims:
        try:
            payload = await asyncio.to_thread(
                id_token.verify_oauth2_token,
                credential,
                Request(),
                self._client_id,
            )
            subject = payload.get("sub")
            email = payload.get("email")
            email_verified = payload.get("email_verified")
            if not isinstance(subject, str) or not isinstance(email, str):
                raise InvalidGoogleCredentialError(GoogleCredentialFailureReason.INVALID_CLAIMS)
            return GoogleIdentityClaims(
                subject=subject,
                email=email,
                email_verified=email_verified is True,
            )
        except (GoogleAuthError, ValueError) as error:
            raise InvalidGoogleCredentialError(classify_verification_failure(error)) from None
