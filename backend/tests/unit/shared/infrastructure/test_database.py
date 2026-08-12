from unittest.mock import AsyncMock, MagicMock

import pytest

from md2blog.shared.infrastructure import database


class SessionContext:
    def __init__(self, session: AsyncMock) -> None:
        self._session = session

    async def __aenter__(self) -> AsyncMock:
        return self._session

    async def __aexit__(self, *args: object) -> None:
        return None


async def test_session_commits_after_success(monkeypatch: pytest.MonkeyPatch) -> None:
    session = AsyncMock()
    factory = MagicMock(return_value=SessionContext(session))
    monkeypatch.setattr(database, "get_session_factory", lambda: factory)

    generator = database.get_session()
    yielded = await anext(generator)
    with pytest.raises(StopAsyncIteration):
        await anext(generator)

    assert yielded is session
    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()


async def test_session_rolls_back_after_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    session = AsyncMock()
    factory = MagicMock(return_value=SessionContext(session))
    monkeypatch.setattr(database, "get_session_factory", lambda: factory)

    generator = database.get_session()
    await anext(generator)
    with pytest.raises(RuntimeError):
        await generator.athrow(RuntimeError("failed"))

    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()
