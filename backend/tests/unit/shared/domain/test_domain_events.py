from datetime import UTC, datetime

from md2blog.shared.domain.events import DomainEvent
from md2blog.shared.domain.tsid import TSID


def test_domain_event_exposes_concrete_event_type() -> None:
    event = DomainEvent(
        event_id=TSID(1),
        aggregate_id=TSID(2),
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert event.event_type == "DomainEvent"
