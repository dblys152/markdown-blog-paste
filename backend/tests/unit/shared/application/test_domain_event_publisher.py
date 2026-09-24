from datetime import UTC, datetime

import pytest

from md2blog.shared.application.events import DomainEventPublisher
from md2blog.shared.domain.events import DomainEvent
from md2blog.shared.domain.tsid import TSID


@pytest.mark.asyncio
async def test_publisher_invokes_every_subscribed_handler_in_registration_order() -> None:
    publisher = DomainEventPublisher()
    handled: list[str] = []

    async def first(event: DomainEvent) -> None:
        handled.append(f"first:{event.event_type}")

    async def second(event: DomainEvent) -> None:
        handled.append(f"second:{event.event_type}")

    publisher.subscribe(DomainEvent, first)
    publisher.subscribe(DomainEvent, second)
    event = DomainEvent(
        event_id=TSID(1),
        aggregate_id=TSID(2),
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    await publisher.publish(event)

    assert handled == ["first:DomainEvent", "second:DomainEvent"]


@pytest.mark.asyncio
async def test_publisher_ignores_unsubscribed_event() -> None:
    publisher = DomainEventPublisher()
    event = DomainEvent(
        event_id=TSID(1),
        aggregate_id=TSID(2),
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    await publisher.publish(event)
