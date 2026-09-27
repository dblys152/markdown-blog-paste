from collections.abc import Callable

import pytest
from google.auth import exceptions as google_exceptions
from google.oauth2 import id_token

from md2blog.modules.identity.application.port.outbound.google_identity import (
    GoogleCredentialFailureReason,
    InvalidGoogleCredentialError,
)
from md2blog.modules.identity.infrastructure.google_identity import GoogleIdTokenVerifier


@pytest.mark.parametrize(
    ("error_factory", "expected_reason"),
    [
        (
            lambda: google_exceptions.InvalidValue("Token has wrong audience"),
            GoogleCredentialFailureReason.AUDIENCE_MISMATCH,
        ),
        (
            lambda: google_exceptions.InvalidValue("Token expired"),
            GoogleCredentialFailureReason.TOKEN_EXPIRED,
        ),
        (
            lambda: google_exceptions.InvalidValue("Token used too early; check clock"),
            GoogleCredentialFailureReason.TOKEN_NOT_YET_VALID,
        ),
        (
            lambda: google_exceptions.GoogleAuthError("Wrong issuer"),
            GoogleCredentialFailureReason.INVALID_ISSUER,
        ),
        (
            lambda: google_exceptions.TransportError("certificate endpoint unavailable"),
            GoogleCredentialFailureReason.CERTIFICATE_FETCH_FAILED,
        ),
        (
            lambda: google_exceptions.MalformedError("Could not verify token signature"),
            GoogleCredentialFailureReason.SIGNATURE_VERIFICATION_FAILED,
        ),
        (
            lambda: ValueError("malformed credential"),
            GoogleCredentialFailureReason.INVALID_TOKEN,
        ),
    ],
)
async def test_verifier_classifies_failure_without_exposing_provider_message(
    monkeypatch: pytest.MonkeyPatch,
    error_factory: Callable[[], Exception],
    expected_reason: GoogleCredentialFailureReason,
) -> None:
    provider_error = error_factory()

    def fail_verification(*_: object, **__: object) -> dict[str, object]:
        raise provider_error

    monkeypatch.setattr(id_token, "verify_oauth2_token", fail_verification)

    with pytest.raises(InvalidGoogleCredentialError) as raised:
        await GoogleIdTokenVerifier("client-id").verify("sensitive-token")

    assert raised.value.reason is expected_reason
    assert raised.value.__cause__ is None
    assert "sensitive-token" not in str(raised.value)
