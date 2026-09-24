from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from md2blog.modules.identity.domain.account_confirmation_token import (
    AccountConfirmationToken,
    AccountConfirmationTokenPurpose,
)
from md2blog.modules.identity.infrastructure.models import AccountConfirmationTokenModel
from md2blog.shared.domain.tsid import TSID


class SqlAlchemyAccountConfirmationTokenRepository:
    def __init__(self, session: AsyncSession, purpose: AccountConfirmationTokenPurpose) -> None:
        self._session = session
        self._purpose = purpose

    async def add(self, token: AccountConfirmationToken) -> None:
        if token.purpose != self._purpose:
            raise ValueError("token purpose does not match repository")
        self._session.add(self._to_model(token))
        await self._session.flush()

    async def find_by_token_hash_for_update(
        self, token_hash: str
    ) -> AccountConfirmationToken | None:
        statement = (
            select(AccountConfirmationTokenModel)
            .where(
                AccountConfirmationTokenModel.token_hash == token_hash,
                AccountConfirmationTokenModel.purpose == self._purpose.value,
            )
            .with_for_update()
        )
        model = await self._session.scalar(statement)
        return None if model is None else self._to_domain(model)

    async def find_latest_by_user_id(self, user_id: TSID) -> AccountConfirmationToken | None:
        statement = (
            select(AccountConfirmationTokenModel)
            .where(
                AccountConfirmationTokenModel.user_id == user_id.value,
                AccountConfirmationTokenModel.purpose == self._purpose.value,
            )
            .order_by(AccountConfirmationTokenModel.created_at.desc())
            .limit(1)
        )
        model = await self._session.scalar(statement)
        return None if model is None else self._to_domain(model)

    async def save(self, token: AccountConfirmationToken) -> None:
        if token.purpose != self._purpose:
            raise ValueError("token purpose does not match repository")
        model = await self._session.get(AccountConfirmationTokenModel, token.id.value)
        if model is None or model.purpose != self._purpose.value:
            raise LookupError("auth token not found")
        model.used_at = token.used_at
        model.revoked_at = token.revoked_at
        await self._session.flush()

    async def count_created_since(self, user_id: TSID, since: datetime) -> int:
        statement = (
            select(func.count())
            .select_from(AccountConfirmationTokenModel)
            .where(
                AccountConfirmationTokenModel.user_id == user_id.value,
                AccountConfirmationTokenModel.purpose == self._purpose.value,
                AccountConfirmationTokenModel.created_at >= since,
            )
        )
        return int(await self._session.scalar(statement) or 0)

    @staticmethod
    def _to_model(token: AccountConfirmationToken) -> AccountConfirmationTokenModel:
        return AccountConfirmationTokenModel(
            id=token.id.value,
            user_id=token.user_id.value,
            purpose=token.purpose.value,
            token_hash=token.token_hash,
            expires_at=token.expires_at,
            used_at=token.used_at,
            revoked_at=token.revoked_at,
            created_at=token.created_at,
        )

    @staticmethod
    def _to_domain(model: AccountConfirmationTokenModel) -> AccountConfirmationToken:
        return AccountConfirmationToken(
            id=TSID(model.id),
            user_id=TSID(model.user_id),
            purpose=AccountConfirmationTokenPurpose(model.purpose),
            token_hash=model.token_hash,
            expires_at=model.expires_at,
            used_at=model.used_at,
            revoked_at=model.revoked_at,
            created_at=model.created_at,
        )
