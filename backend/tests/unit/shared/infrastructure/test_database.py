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


async def test_session_only_manages_lifecycle(monkeypatch: pytest.MonkeyPatch) -> None:
    session = AsyncMock()
    factory = MagicMock(return_value=SessionContext(session))
    monkeypatch.setattr(database, "get_session_factory", lambda: factory)

    generator = database.get_session()
    yielded = await anext(generator)
    with pytest.raises(StopAsyncIteration):
        await anext(generator)

    assert yielded is session
    session.commit.assert_not_awaited()
    session.rollback.assert_not_awaited()


async def test_session_does_not_own_rollback_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    session = AsyncMock()
    factory = MagicMock(return_value=SessionContext(session))
    monkeypatch.setattr(database, "get_session_factory", lambda: factory)

    generator = database.get_session()
    await anext(generator)
    with pytest.raises(RuntimeError):
        await generator.athrow(RuntimeError("failed"))

    session.rollback.assert_not_awaited()
    session.commit.assert_not_awaited()


async def test_unit_of_work_commits_after_success() -> None:
    session = AsyncMock()

    async with database.SqlAlchemyUnitOfWork(session):
        pass

    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()


async def test_unit_of_work_rolls_back_after_failure() -> None:
    session = AsyncMock()

    with pytest.raises(RuntimeError):
        async with database.SqlAlchemyUnitOfWork(session):
            raise RuntimeError("failed")

    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()


async def test_nested_unit_of_work_commits_only_at_outer_boundary() -> None:
    session = AsyncMock()
    unit_of_work = database.SqlAlchemyUnitOfWork(session)

    async with unit_of_work:
        async with unit_of_work:
            pass
        session.commit.assert_not_awaited()

    session.commit.assert_awaited_once()


async def test_nested_unit_of_work_rolls_back_outer_transaction() -> None:
    session = AsyncMock()
    unit_of_work = database.SqlAlchemyUnitOfWork(session)

    with pytest.raises(RuntimeError):
        async with unit_of_work:
            async with unit_of_work:
                raise RuntimeError("failed")

    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()
