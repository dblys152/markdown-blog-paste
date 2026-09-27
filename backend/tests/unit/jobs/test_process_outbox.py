from datetime import UTC, datetime

from md2blog.jobs.process_outbox import complete_message, safe_error_detail
from md2blog.modules.identity.application.port.outbound.email import EmailDeliveryError
from md2blog.shared.application.event_records import OutboxMessageStatus
from md2blog.shared.infrastructure.event_models import OutboxMessageModel


def test_complete_message_preserves_payload() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    payload = {"to": "user@example.com", "encrypted_token": "encrypted"}
    message = OutboxMessageModel(
        id=1,
        event_id=2,
        event_type="EmailVerificationRequested",
        aggregate_id=3,
        payload=payload,
        status=OutboxMessageStatus.PROCESSING.value,
        retry_count=0,
        available_at=now,
        occurred_at=now,
        locked_at=now,
        processed_at=None,
        last_error=None,
        created_at=now,
    )

    complete_message(message, now)

    assert message.status == OutboxMessageStatus.COMPLETED.value
    assert message.payload == payload
    assert message.processed_at == now


def test_outbox_failure_detail_uses_sanitized_email_delivery_error() -> None:
    detail, provider_code = safe_error_detail(
        EmailDeliveryError("authentication_failed", 535)
    )

    assert detail == "email delivery failed: reason=authentication_failed, provider_code=535"
    assert provider_code == 535


def test_outbox_failure_detail_hides_unknown_exception_message() -> None:
    detail, provider_code = safe_error_detail(RuntimeError("secret-token"))

    assert detail == "RuntimeError"
    assert provider_code is None
