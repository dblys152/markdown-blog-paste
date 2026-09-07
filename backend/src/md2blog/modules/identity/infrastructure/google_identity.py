import asyncio

from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2 import id_token

from md2blog.modules.identity.application.port.outbound.google_identity import (
    GoogleIdentityClaims,
    InvalidGoogleCredentialError,
)


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
                raise InvalidGoogleCredentialError
            return GoogleIdentityClaims(
                subject=subject,
                email=email,
                email_verified=email_verified is True,
            )
        except (GoogleAuthError, ValueError) as error:
            raise InvalidGoogleCredentialError from error
