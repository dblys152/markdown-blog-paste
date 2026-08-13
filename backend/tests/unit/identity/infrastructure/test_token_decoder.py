from datetime import UTC, datetime, timedelta

import jwt
import pytest

from md2blog.modules.identity.application.port.outbound.security import InvalidAccessTokenError
from md2blog.modules.identity.infrastructure.tokens import JwtAccessTokenDecoder
from md2blog.shared.domain.tsid import TSID

SECRET = "test-secret-that-is-at-least-32-bytes-long"


def create_token(**overrides: object) -> str:
    now = datetime.now(UTC)
    payload: dict[str, object] = {
        "sub": "123456789",
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=15),
    }
    payload.update(overrides)
    return jwt.encode(payload, SECRET, algorithm="HS256")


def test_decoder_returns_tsid_subject() -> None:
    assert JwtAccessTokenDecoder(SECRET).decode_subject(create_token()) == TSID(123456789)


@pytest.mark.parametrize(
    "token",
    [
        create_token(type="refresh"),
        create_token(sub="invalid"),
        create_token(exp=datetime.now(UTC) - timedelta(seconds=1)),
        jwt.encode({"sub": "123456789"}, "different-secret-that-is-32-bytes", algorithm="HS256"),
    ],
)
def test_decoder_rejects_invalid_access_tokens(token: str) -> None:
    with pytest.raises(InvalidAccessTokenError):
        JwtAccessTokenDecoder(SECRET).decode_subject(token)
