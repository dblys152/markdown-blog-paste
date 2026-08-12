from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from md2blog.modules.identity.domain.auth_session import AuthSession
from md2blog.modules.identity.infrastructure.models import AuthSessionModel
from md2blog.shared.domain.tsid import TSID


class SqlAlchemyAuthSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, session: AuthSession) -> None:
        self._session.add(self._to_model(session))
        await self._session.commit()

    async def find_by_token_hash(self, token_hash: str) -> AuthSession | None:
        statement = select(AuthSessionModel).where(
            AuthSessionModel.refresh_token_hash == token_hash
        )
        model = await self._session.scalar(statement)
        return None if model is None else self._to_domain(model)

    async def replace(self, previous: AuthSession, replacement: AuthSession) -> None:
        model = await self._session.get(AuthSessionModel, previous.id.value)
        if model is None:
            raise LookupError("refresh session not found")
        model.revoked_at = previous.revoked_at
        model.replaced_by_token_hash = previous.replaced_by_token_hash
        self._session.add(self._to_model(replacement))
        await self._session.commit()

    @staticmethod
    def _to_model(session: AuthSession) -> AuthSessionModel:
        return AuthSessionModel(
            id=session.id.value,
            user_id=session.user_id.value,
            refresh_token_hash=session.refresh_token_hash,
            expires_at=session.expires_at,
            revoked_at=session.revoked_at,
            replaced_by_token_hash=session.replaced_by_token_hash,
            user_agent=session.user_agent,
            ip_address=session.ip_address,
            created_at=session.created_at,
        )

    @staticmethod
    def _to_domain(model: AuthSessionModel) -> AuthSession:
        return AuthSession(
            id=TSID(model.id),
            user_id=TSID(model.user_id),
            refresh_token_hash=model.refresh_token_hash,
            expires_at=model.expires_at,
            revoked_at=model.revoked_at,
            replaced_by_token_hash=model.replaced_by_token_hash,
            user_agent=model.user_agent,
            ip_address=model.ip_address,
            created_at=model.created_at,
        )
