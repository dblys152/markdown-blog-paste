from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from md2blog.modules.identity.domain.password_reset import PasswordResetToken
from md2blog.modules.identity.infrastructure.models import PasswordResetTokenModel
from md2blog.shared.domain.tsid import TSID


class SqlAlchemyPasswordResetTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, token: PasswordResetToken) -> None:
        self._session.add(self._to_model(token))
        await self._session.flush()

    async def find_by_token_hash_for_update(
        self,
        token_hash: str,
    ) -> PasswordResetToken | None:
        statement = (
            select(PasswordResetTokenModel)
            .where(PasswordResetTokenModel.token_hash == token_hash)
            .with_for_update()
        )
        model = await self._session.scalar(statement)
        return None if model is None else self._to_domain(model)

    async def find_latest_by_user_id(self, user_id: TSID) -> PasswordResetToken | None:
        statement = (
            select(PasswordResetTokenModel)
            .where(PasswordResetTokenModel.user_id == user_id.value)
            .order_by(PasswordResetTokenModel.created_at.desc())
            .limit(1)
        )
        model = await self._session.scalar(statement)
        return None if model is None else self._to_domain(model)

    async def save(self, token: PasswordResetToken) -> None:
        model = await self._session.get(PasswordResetTokenModel, token.id.value)
        if model is None:
            raise LookupError("password reset token not found")
        model.used_at = token.used_at
        model.revoked_at = token.revoked_at
        await self._session.flush()

    async def count_created_since(self, user_id: TSID, since: datetime) -> int:
        statement = select(func.count()).select_from(PasswordResetTokenModel).where(
            PasswordResetTokenModel.user_id == user_id.value,
            PasswordResetTokenModel.created_at >= since,
        )
        return int(await self._session.scalar(statement) or 0)

    @staticmethod
    def _to_model(token: PasswordResetToken) -> PasswordResetTokenModel:
        return PasswordResetTokenModel(
            id=token.id.value,
            user_id=token.user_id.value,
            token_hash=token.token_hash,
            expires_at=token.expires_at,
            used_at=token.used_at,
            revoked_at=token.revoked_at,
            created_at=token.created_at,
        )

    @staticmethod
    def _to_domain(model: PasswordResetTokenModel) -> PasswordResetToken:
        return PasswordResetToken(
            id=TSID(model.id),
            user_id=TSID(model.user_id),
            token_hash=model.token_hash,
            expires_at=model.expires_at,
            used_at=model.used_at,
            revoked_at=model.revoked_at,
            created_at=model.created_at,
        )
