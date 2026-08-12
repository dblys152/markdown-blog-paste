from datetime import timedelta

import jwt

from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import DisplayName, Email, PasswordHash
from md2blog.modules.identity.infrastructure.tokens import JwtAccessTokenIssuer
from md2blog.shared.domain.tsid import TSID


def test_access_token_contains_string_user_id_and_expiration() -> None:
    user = User(
        id=TSID(123456789),
        email=Email("user@example.com"),
        password_hash=PasswordHash("hash"),
        display_name=DisplayName("User"),
    )
    secret = "test-secret-that-is-at-least-32-bytes-long"
    issuer = JwtAccessTokenIssuer(secret, timedelta(minutes=15))

    token = issuer.issue(user)
    payload = jwt.decode(token, secret, algorithms=["HS256"])

    assert payload["sub"] == "123456789"
    assert payload["type"] == "access"
    assert payload["exp"] > payload["iat"]
