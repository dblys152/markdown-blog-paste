from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import TypeVar, cast

from md2blog.shared.domain.events import DomainEvent

EventT = TypeVar("EventT", bound=DomainEvent)
type DomainEventHandler = Callable[[DomainEvent], Awaitable[None]]


class DomainEventPublisher:
    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[DomainEventHandler]] = defaultdict(list)

    def subscribe(
        self,
        event_type: type[EventT],
        handler: Callable[[EventT], Awaitable[None]],
    ) -> None:
        self._handlers[event_type].append(cast(DomainEventHandler, handler))

    async def publish(self, event: DomainEvent) -> None:
        for handler in self._handlers[type(event)]:
            await handler(event)
