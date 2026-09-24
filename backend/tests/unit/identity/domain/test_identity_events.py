from datetime import UTC, datetime

from md2blog.modules.identity.domain.events import EmailVerificationRequested
from md2blog.modules.identity.domain.value_objects import DisplayName, Email
from md2blog.shared.domain.tsid import TSID


def test_email_verification_requested_is_a_domain_event() -> None:
    event = EmailVerificationRequested(
        event_id=TSID(1),
        aggregate_id=TSID(2),
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        user_id=TSID(2),
        email=Email("user@example.com"),
        display_name=DisplayName("사용자"),
        raw_token="raw-token",
    )

    assert event.event_type == "EmailVerificationRequested"
    assert event.aggregate_id == event.user_id
