from datetime import UTC, datetime

import pytest

from md2blog.modules.identity.application.event_handlers import (
    EmailVerificationRequestedHandler,
    PasswordResetRequestedHandler,
    SecurityAuditLogHandler,
)
from md2blog.modules.identity.domain.events import (
    AuthenticationFailed,
    EmailVerificationRequested,
    PasswordResetRequested,
)
from md2blog.modules.identity.domain.value_objects import DisplayName, Email
from md2blog.shared.application.event_records import OutboxMessage, SecurityAuditLog
from md2blog.shared.domain.tsid import TSID


class FakeOutboxRepository:
    def __init__(self) -> None:
        self.messages: list[OutboxMessage] = []

    async def add(self, message: OutboxMessage) -> None:
        self.messages.append(message)


class FakeAuditRepository:
    def __init__(self) -> None:
        self.logs: list[SecurityAuditLog] = []

    async def add(self, log: SecurityAuditLog) -> None:
        self.logs.append(log)


class ReversingCipher:
    def encrypt(self, payload: str) -> str:
        return payload[::-1]

    def decrypt(self, encrypted_value: str) -> str:
        return encrypted_value[::-1]


@pytest.mark.asyncio
async def test_email_verification_event_encrypts_only_sensitive_token() -> None:
    repository = FakeOutboxRepository()
    handler = EmailVerificationRequestedHandler(
        repository,
        ReversingCipher(),
        "https://md2blog.test",
    )
    event = EmailVerificationRequested(
        event_id=TSID(1),
        aggregate_id=TSID(2),
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        user_id=TSID(2),
        email=Email("user@example.com"),
        display_name=DisplayName("사용자"),
        raw_token="secret token",
    )

    await handler.handle(event)

    message = repository.messages[0]
    payload = message.payload
    assert message.event_id == event.event_id
    assert payload["to"] == "user@example.com"
    assert payload["action_url"] == "https://md2blog.test/verify-email"
    assert payload["encrypted_token"] == "nekot terces"
    assert "secret token" not in str(payload)


@pytest.mark.asyncio
async def test_password_reset_event_is_stored_with_its_own_follow_up_payload() -> None:
    repository = FakeOutboxRepository()
    handler = PasswordResetRequestedHandler(
        repository,
        ReversingCipher(),
        "https://md2blog.test",
    )
    event = PasswordResetRequested(
        event_id=TSID(1),
        aggregate_id=TSID(2),
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        user_id=TSID(2),
        email=Email("user@example.com"),
        display_name=DisplayName("사용자"),
        raw_token="reset-token",
    )

    await handler.handle(event)

    payload = repository.messages[0].payload
    assert payload["action_url"] == "https://md2blog.test/reset-password"
    assert payload["encrypted_token"] == "nekot-teser"
    assert payload["subject"] == "[MD2Blog] 비밀번호를 재설정해 주세요"


@pytest.mark.asyncio
async def test_security_event_is_stored_as_append_only_audit_record() -> None:
    repository = FakeAuditRepository()
    handler = SecurityAuditLogHandler(repository)
    event = AuthenticationFailed(
        event_id=TSID(1),
        aggregate_id=TSID(2),
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        user_id=TSID(2),
    )

    await handler.handle(event)

    log = repository.logs[0]
    assert log.event_id == event.event_id
    assert log.event_type == "AuthenticationFailed"
    assert log.user_id == event.user_id
