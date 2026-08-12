from datetime import UTC, datetime, timedelta

import jwt

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
