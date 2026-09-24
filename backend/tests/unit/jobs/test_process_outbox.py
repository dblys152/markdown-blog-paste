from datetime import UTC, datetime

from md2blog.jobs.process_outbox import complete_message
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
