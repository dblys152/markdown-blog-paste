import secrets
from datetime import UTC, datetime, timedelta
from hashlib import sha256

import jwt

from md2blog.modules.identity.application.port.outbound.security import (
    InvalidAccessTokenError,
    RefreshToken,
)
from md2blog.modules.identity.domain.user import User
from md2blog.shared.domain.tsid import TSID


class JwtAccessTokenIssuer:
    def __init__(self, secret_key: str, ttl: timedelta) -> None:
        self._secret_key = secret_key
        self._ttl = ttl

    def issue(self, user: User) -> str:
        now = datetime.now(UTC)
        return jwt.encode(
            {
                "sub": str(user.id),
                "type": "access",
                "iat": now,
                "exp": now + self._ttl,
            },
            self._secret_key,
            algorithm="HS256",
        )


class JwtAccessTokenDecoder:
    def __init__(self, secret_key: str) -> None:
        self._secret_key = secret_key

    def decode_subject(self, token: str) -> TSID:
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=["HS256"],
                options={"require": ["sub", "type", "iat", "exp"]},
            )
            if payload["type"] != "access" or not isinstance(payload["sub"], str):
                raise InvalidAccessTokenError
            return TSID.from_string(payload["sub"])
        except (jwt.PyJWTError, KeyError, TypeError, ValueError) as error:
            raise InvalidAccessTokenError from error


class SecureRefreshTokenManager:
    def generate(self) -> RefreshToken:
        raw = secrets.token_urlsafe(48)
        return RefreshToken(raw=raw, token_hash=self.hash(raw))

    def hash(self, raw_token: str) -> str:
        return sha256(raw_token.encode("utf-8")).hexdigest()


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)
