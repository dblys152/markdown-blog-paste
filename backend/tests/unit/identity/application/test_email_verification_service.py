from datetime import UTC, datetime, timedelta

import pytest

from md2blog.modules.identity.application.port.outbound.account_confirmation_token import (
    GeneratedAccountConfirmationToken,
)
from md2blog.modules.identity.application.service.email_verification import (
    ConfirmEmailVerification,
    EmailVerificationCooldownError,
    EmailVerificationPolicy,
    InvalidEmailVerificationTokenError,
    IssueEmailVerification,
)
from md2blog.modules.identity.domain.account_confirmation_token import (
    AccountConfirmationToken,
    AccountConfirmationTokenPurpose,
)
from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import DisplayName, Email, PasswordHash
from md2blog.shared.application.events import DomainEventPublisher
from md2blog.shared.domain.events import DomainEvent
from md2blog.shared.domain.tsid import TSID

NOW = datetime(2026, 8, 27, 12, tzinfo=UTC)


class FixedClock:
    def now(self) -> datetime:
        return NOW


class StubTokenManager:
    def generate(self) -> GeneratedAccountConfirmationToken:
        return GeneratedAccountConfirmationToken(raw="raw-token", token_hash="token-hash")

    def hash(self, raw_token: str) -> str:
        return "token-hash" if raw_token == "raw-token" else "unknown"


class RecordingEvents(DomainEventPublisher):
    def __init__(self) -> None:
        super().__init__()
        self.events: list[DomainEvent] = []

    async def publish(self, event: DomainEvent) -> None:
        self.events.append(event)


class InMemoryTokens:
    def __init__(self, token: AccountConfirmationToken | None = None) -> None:
        self.tokens = [] if token is None else [token]

    async def add(self, token: AccountConfirmationToken) -> None:
        self.tokens.append(token)

    async def find_latest_by_user_id(self, user_id: TSID) -> AccountConfirmationToken | None:
        matches = [token for token in self.tokens if token.user_id == user_id]
        return max(matches, key=lambda token: token.created_at) if matches else None

    async def find_by_token_hash_for_update(
        self, token_hash: str
    ) -> AccountConfirmationToken | None:
        return next((token for token in self.tokens if token.token_hash == token_hash), None)

    async def save(self, token: AccountConfirmationToken) -> None:
        self.tokens = [token if current.id == token.id else current for current in self.tokens]

    async def count_created_since(self, user_id: TSID, since: datetime) -> int:
        return sum(token.user_id == user_id and token.created_at >= since for token in self.tokens)


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
    events = RecordingEvents()
    service = IssueEmailVerification(
        tokens=tokens,
        token_manager=StubTokenManager(),
        events=events,
        clock=FixedClock(),
        policy=make_policy(),
    )

    await service.execute(make_user())

    assert tokens.tokens[0].token_hash == "token-hash"
    assert tokens.tokens[0].expires_at == NOW + timedelta(hours=24)
    assert events.events[0].event_type == "EmailVerificationRequested"


@pytest.mark.asyncio
async def test_issue_rejects_resend_during_cooldown() -> None:
    token = AccountConfirmationToken.issue(
        token_id=TSID(2),
        user_id=TSID(1),
        purpose=AccountConfirmationTokenPurpose.EMAIL_VERIFICATION,
        token_hash="previous",
        issued_at=NOW - timedelta(seconds=30),
        expires_at=NOW + timedelta(hours=1),
    )
    service = IssueEmailVerification(
        tokens=InMemoryTokens(token),
        token_manager=StubTokenManager(),
        events=RecordingEvents(),
        clock=FixedClock(),
        policy=make_policy(),
    )

    with pytest.raises(EmailVerificationCooldownError) as error:
        await service.execute(make_user())

    assert error.value.retry_after_seconds == 30


@pytest.mark.asyncio
async def test_confirm_marks_token_and_user_as_verified() -> None:
    token = AccountConfirmationToken.issue(
        token_id=TSID(2),
        user_id=TSID(1),
        purpose=AccountConfirmationTokenPurpose.EMAIL_VERIFICATION,
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
        events=RecordingEvents(),
        clock=FixedClock(),
    )

    result = await service.execute("raw-token")

    assert result.email_verified_at == NOW
    assert users.user.email_verified_at == NOW
    assert tokens.tokens[0].used_at == NOW


async def test_password_reset_token_cannot_verify_email() -> None:
    token = AccountConfirmationToken.issue(
        token_id=TSID(2),
        user_id=TSID(1),
        purpose=AccountConfirmationTokenPurpose.PASSWORD_RESET,
        token_hash="token-hash",
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(hours=1),
    )
    users = InMemoryUsers(make_user())
    service = ConfirmEmailVerification(
        users=users,  # type: ignore[arg-type]
        tokens=InMemoryTokens(token),
        token_manager=StubTokenManager(),
        events=RecordingEvents(),
        clock=FixedClock(),
    )

    with pytest.raises(InvalidEmailVerificationTokenError):
        await service.execute("raw-token")
    assert users.user.email_verified_at is None
