import pytest

from md2blog.shared.application.outbox import (
    OutboxMessageDispatcher,
    OutboxMessageHandlerNotFoundError,
)


class RecordingHandler:
    def __init__(self) -> None:
        self.payloads: list[dict[str, str]] = []

    async def handle(self, payload: dict[str, str]) -> None:
        self.payloads.append(payload)


@pytest.mark.asyncio
async def test_dispatcher_selects_handler_by_event_type() -> None:
    dispatcher = OutboxMessageDispatcher()
    handler = RecordingHandler()
    dispatcher.register("EmailVerificationRequested", handler)
    payload = {"to": "user@example.com"}

    await dispatcher.dispatch("EmailVerificationRequested", payload)

    assert handler.payloads == [payload]


@pytest.mark.asyncio
async def test_dispatcher_rejects_unregistered_event_type() -> None:
    dispatcher = OutboxMessageDispatcher()

    with pytest.raises(OutboxMessageHandlerNotFoundError):
        await dispatcher.dispatch("UnknownEvent", {})
