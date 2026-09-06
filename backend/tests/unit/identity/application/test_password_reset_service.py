from datetime import UTC, datetime, timedelta

from md2blog.modules.identity.application.port.outbound.email import (
    GeneratedPasswordResetToken,
    OutboundEmail,
)
from md2blog.modules.identity.application.service.password_reset import (
    ConfirmPasswordReset,
    PasswordResetPolicy,
    RequestPasswordReset,
)
from md2blog.modules.identity.domain.commands import (
    ConfirmPasswordResetCommand,
    RequestPasswordResetCommand,
)
from md2blog.modules.identity.domain.password_reset import PasswordResetToken
from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import (
    DisplayName,
    Email,
    PasswordHash,
    RawPassword,
)
from md2blog.shared.domain.tsid import TSID

NOW = datetime(2026, 9, 6, 12, tzinfo=UTC)


class Clock:
    def now(self) -> datetime:
        return NOW


class TokenManager:
    def generate(self) -> GeneratedPasswordResetToken:
        return GeneratedPasswordResetToken(raw="raw-token", token_hash="token-hash")

    def hash(self, raw_token: str) -> str:
        return "token-hash" if raw_token == "raw-token" else "unknown"


class Emails:
    def __init__(self) -> None:
        self.messages: list[OutboundEmail] = []

    async def send(self, message: OutboundEmail) -> None:
        self.messages.append(message)


class Tokens:
    def __init__(self, token: PasswordResetToken | None = None) -> None:
        self.tokens = [] if token is None else [token]

    async def add(self, token: PasswordResetToken) -> None:
        self.tokens.append(token)

    async def find_by_token_hash_for_update(self, token_hash: str) -> PasswordResetToken | None:
        return next((token for token in self.tokens if token.token_hash == token_hash), None)

    async def find_latest_by_user_id(self, user_id: TSID) -> PasswordResetToken | None:
        matches = [token for token in self.tokens if token.user_id == user_id]
        return max(matches, key=lambda token: token.created_at) if matches else None

    async def save(self, token: PasswordResetToken) -> None:
        self.tokens = [token if current.id == token.id else current for current in self.tokens]

    async def count_created_since(self, user_id: TSID, since: datetime) -> int:
        return sum(token.user_id == user_id and token.created_at >= since for token in self.tokens)


class Users:
    def __init__(self, user: User | None) -> None:
        self.user = user

    async def find_by_email(self, email: Email) -> User | None:
        return self.user if self.user and self.user.email == email else None

    async def find_by_id(self, user_id: int) -> User | None:
        return self.user if self.user and self.user.id.value == user_id else None

    async def save(self, user: User) -> None:
        self.user = user


class Passwords:
    def hash(self, password: RawPassword) -> PasswordHash:
        return PasswordHash(f"hashed:{password.value}")


class Sessions:
    def __init__(self) -> None:
        self.revoked_user_id: TSID | None = None

    async def revoke_all_by_user_id(self, user_id: TSID, revoked_at: datetime) -> None:
        self.revoked_user_id = user_id


def make_user() -> User:
    return User(
        id=TSID(1),
        email=Email("user@example.com"),
        password_hash=PasswordHash("old-hash"),
        display_name=DisplayName("User"),
        email_verified_at=NOW,
    )


def make_policy() -> PasswordResetPolicy:
    return PasswordResetPolicy(
        token_ttl=timedelta(hours=1),
        resend_cooldown=timedelta(seconds=60),
        daily_limit=5,
    )


async def test_request_stores_hashed_token_and_sends_reset_link() -> None:
    tokens = Tokens()
    emails = Emails()
    service = RequestPasswordReset(
        users=Users(make_user()),  # type: ignore[arg-type]
        tokens=tokens,
        token_manager=TokenManager(),
        email_sender=emails,
        clock=Clock(),
        policy=make_policy(),
        frontend_url="https://md2blog.pages.dev",
    )

    await service.execute(RequestPasswordResetCommand(email=Email("user@example.com")))

    assert tokens.tokens[0].token_hash == "token-hash"
    assert tokens.tokens[0].expires_at == NOW + timedelta(hours=1)
    assert "https://md2blog.pages.dev/reset-password?token=raw-token" in emails.messages[0].html


async def test_request_does_nothing_for_unknown_email() -> None:
    emails = Emails()
    service = RequestPasswordReset(
        users=Users(None),  # type: ignore[arg-type]
        tokens=Tokens(),
        token_manager=TokenManager(),
        email_sender=emails,
        clock=Clock(),
        policy=make_policy(),
        frontend_url="https://md2blog.pages.dev",
    )

    await service.execute(RequestPasswordResetCommand(email=Email("unknown@example.com")))

    assert emails.messages == []


async def test_confirm_changes_password_and_revokes_all_sessions() -> None:
    token = PasswordResetToken.issue(
        token_id=TSID(2),
        user_id=TSID(1),
        token_hash="token-hash",
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(hours=1),
    )
    users = Users(make_user())
    tokens = Tokens(token)
    sessions = Sessions()
    service = ConfirmPasswordReset(
        users=users,  # type: ignore[arg-type]
        sessions=sessions,  # type: ignore[arg-type]
        tokens=tokens,
        token_manager=TokenManager(),
        password_hasher=Passwords(),  # type: ignore[arg-type]
        clock=Clock(),
    )

    await service.execute(
        ConfirmPasswordResetCommand(
            token="raw-token",
            new_password=RawPassword("new-password"),
        )
    )

    assert users.user is not None
    assert users.user.password_hash == PasswordHash("hashed:new-password")
    assert tokens.tokens[0].used_at == NOW
    assert sessions.revoked_user_id == TSID(1)
