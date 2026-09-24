from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from md2blog.modules.identity.domain.login_failure_state import LoginFailureState
from md2blog.modules.identity.infrastructure.models import LoginFailureStateModel
from md2blog.shared.domain.tsid import TSID


class SqlAlchemyLoginFailureStateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_for_update(self, user_id: TSID) -> LoginFailureState | None:
        await self._session.execute(
            text("SELECT pg_advisory_xact_lock(:user_id)"),
            {"user_id": user_id.value},
        )
        statement = (
            select(LoginFailureStateModel)
            .where(LoginFailureStateModel.user_id == user_id.value)
            .with_for_update()
        )
        model = await self._session.scalar(statement)
        return None if model is None else self._to_domain(model)

    async def add(self, state: LoginFailureState) -> None:
        self._session.add(self._to_model(state))
        await self._session.flush()

    async def save(self, state: LoginFailureState) -> None:
        model = await self._session.get(LoginFailureStateModel, state.user_id.value)
        if model is None:
            raise LookupError("login failure state not found")
        model.failure_count = state.failure_count
        model.window_started_at = state.window_started_at
        model.blocked_until = state.blocked_until
        await self._session.flush()

    async def delete(self, user_id: TSID) -> None:
        await self._session.execute(
            delete(LoginFailureStateModel).where(LoginFailureStateModel.user_id == user_id.value)
        )

    @staticmethod
    def _to_model(state: LoginFailureState) -> LoginFailureStateModel:
        return LoginFailureStateModel(
            user_id=state.user_id.value,
            failure_count=state.failure_count,
            window_started_at=state.window_started_at,
            blocked_until=state.blocked_until,
        )

    @staticmethod
    def _to_domain(model: LoginFailureStateModel) -> LoginFailureState:
        return LoginFailureState(
            user_id=TSID(model.user_id),
            failure_count=model.failure_count,
            window_started_at=model.window_started_at,
            blocked_until=model.blocked_until,
        )
