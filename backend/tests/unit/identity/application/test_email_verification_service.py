from datetime import UTC, datetime, timedelta

import pytest

from md2blog.modules.identity.application.port.outbound.email import (
    GeneratedEmailVerificationToken,
    OutboundEmail,
)
from md2blog.modules.identity.application.service.email_verification import (
    ConfirmEmailVerification,
    EmailVerificationCooldownError,
    EmailVerificationPolicy,
    IssueEmailVerification,
)
from md2blog.modules.identity.domain.email_verification import EmailVerificationToken
from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import DisplayName, Email, PasswordHash
from md2blog.shared.domain.tsid import TSID

NOW = datetime(2026, 8, 27, 12, tzinfo=UTC)


class FixedClock:
    def now(self) -> datetime:
        return NOW


class StubTokenManager:
    def generate(self) -> GeneratedEmailVerificationToken:
        return GeneratedEmailVerificationToken(raw="raw-token", token_hash="token-hash")

    def hash(self, raw_token: str) -> str:
        return "token-hash" if raw_token == "raw-token" else "unknown"


class RecordingEmailSender:
    def __init__(self) -> None:
        self.messages: list[OutboundEmail] = []

    async def send(self, message: OutboundEmail) -> None:
        self.messages.append(message)


class InMemoryTokens:
    def __init__(self, token: EmailVerificationToken | None = None) -> None:
        self.tokens = [] if token is None else [token]

    async def add(self, token: EmailVerificationToken) -> None:
        self.tokens.append(token)

    async def find_latest_by_user_id(self, user_id: TSID) -> EmailVerificationToken | None:
        matches = [token for token in self.tokens if token.user_id == user_id]
        return max(matches, key=lambda token: token.created_at) if matches else None

    async def find_by_token_hash_for_update(
        self, token_hash: str
    ) -> EmailVerificationToken | None:
        return next((token for token in self.tokens if token.token_hash == token_hash), None)

    async def save(self, token: EmailVerificationToken) -> None:
        self.tokens = [token if current.id == token.id else current for current in self.tokens]

    async def count_created_since(self, user_id: TSID, since: datetime) -> int:
        return sum(
            token.user_id == user_id and token.created_at >= since for token in self.tokens
        )


class InMemoryUsers:
    def __init__(self, user: User) -> None:
        self.user = user

    async def find_by_id(self, user_id: int) -> User | None:
        return self.user if self.user.id.value == user_id else None

    async def save(self, user: User) -> None:
        self.user = user


def make_user() -> User:
    return User(
        id=TSID(1),
        email=Email("user@example.com"),
        password_hash=PasswordHash("hash"),
        display_name=DisplayName("User"),
    )


def make_policy() -> EmailVerificationPolicy:
    return EmailVerificationPolicy(
        token_ttl=timedelta(hours=24),
        resend_cooldown=timedelta(seconds=60),
        daily_limit=5,
    )


@pytest.mark.asyncio
async def test_issue_stores_hashed_token_and_sends_verification_link() -> None:
    tokens = InMemoryTokens()
    emails = RecordingEmailSender()
    service = IssueEmailVerification(
        tokens=tokens,
        token_manager=StubTokenManager(),
        email_sender=emails,
        clock=FixedClock(),
        policy=make_policy(),
        frontend_url="https://md2blog.pages.dev/",
    )

    await service.execute(make_user())

    assert tokens.tokens[0].token_hash == "token-hash"
    assert tokens.tokens[0].expires_at == NOW + timedelta(hours=24)
    assert len(emails.messages) == 1
    assert "https://md2blog.pages.dev/verify-email?token=raw-token" in emails.messages[0].html


@pytest.mark.asyncio
async def test_issue_rejects_resend_during_cooldown() -> None:
    token = EmailVerificationToken.issue(
        token_id=TSID(2),
        user_id=TSID(1),
        token_hash="previous",
        issued_at=NOW - timedelta(seconds=30),
        expires_at=NOW + timedelta(hours=1),
    )
    service = IssueEmailVerification(
        tokens=InMemoryTokens(token),
        token_manager=StubTokenManager(),
        email_sender=RecordingEmailSender(),
        clock=FixedClock(),
        policy=make_policy(),
        frontend_url="https://md2blog.pages.dev",
    )

    with pytest.raises(EmailVerificationCooldownError) as error:
        await service.execute(make_user())

    assert error.value.retry_after_seconds == 30


@pytest.mark.asyncio
async def test_confirm_marks_token_and_user_as_verified() -> None:
    token = EmailVerificationToken.issue(
        token_id=TSID(2),
        user_id=TSID(1),
        token_hash="token-hash",
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(hours=1),
    )
    tokens = InMemoryTokens(token)
    users = InMemoryUsers(make_user())
    service = ConfirmEmailVerification(
        users=users,  # type: ignore[arg-type]
        tokens=tokens,
        token_manager=StubTokenManager(),
        clock=FixedClock(),
    )

    result = await service.execute("raw-token")

    assert result.email_verified_at == NOW
    assert users.user.email_verified_at == NOW
    assert tokens.tokens[0].used_at == NOW
