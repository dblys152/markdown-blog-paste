import secrets
from datetime import UTC, datetime, timedelta
from hashlib import sha256

import jwt

from md2blog.modules.identity.application.port.outbound.security import RefreshToken
from md2blog.modules.identity.domain.user import User


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


class SecureRefreshTokenManager:
    def generate(self) -> RefreshToken:
        raw = secrets.token_urlsafe(48)
        return RefreshToken(raw=raw, token_hash=self.hash(raw))

    def hash(self, raw_token: str) -> str:
        return sha256(raw_token.encode("utf-8")).hexdigest()


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)
