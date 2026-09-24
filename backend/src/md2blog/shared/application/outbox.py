from typing import Protocol


class OutboxMessageHandler(Protocol):
    async def handle(self, payload: dict[str, str]) -> None: ...


class OutboxMessageDispatcher:
    def __init__(self) -> None:
        self._handlers: dict[str, OutboxMessageHandler] = {}

    def register(self, event_type: str, handler: OutboxMessageHandler) -> None:
        self._handlers[event_type] = handler

    async def dispatch(self, event_type: str, payload: dict[str, str]) -> None:
        handler = self._handlers.get(event_type)
        if handler is None:
            raise OutboxMessageHandlerNotFoundError(event_type)
        await handler.handle(payload)


class OutboxMessageHandlerNotFoundError(Exception):
    def __init__(self, event_type: str) -> None:
        super().__init__(f"Outbox message handler not found: {event_type}")
