from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from md2blog.modules.identity.domain.user_identity import IdentityProvider, UserIdentity
from md2blog.modules.identity.infrastructure.models import UserIdentityModel
from md2blog.shared.domain.tsid import TSID


class SqlAlchemyUserIdentityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, identity: UserIdentity) -> None:
        self._session.add(
            UserIdentityModel(
                id=identity.id.value,
                user_id=identity.user_id.value,
                provider=identity.provider.value,
                provider_subject=identity.provider_subject,
                provider_email=identity.provider_email,
                created_at=identity.created_at,
            )
        )
        await self._session.flush()

    async def delete(self, identity: UserIdentity) -> None:
        model = await self._session.get(UserIdentityModel, identity.id.value)
        if model is None:
            raise LookupError("user identity not found")
        await self._session.delete(model)
        await self._session.flush()

    async def find_by_provider_subject(
        self,
        provider: IdentityProvider,
        provider_subject: str,
    ) -> UserIdentity | None:
        statement = select(UserIdentityModel).where(
            UserIdentityModel.provider == provider.value,
            UserIdentityModel.provider_subject == provider_subject,
        )
        model = await self._session.scalar(statement)
        return None if model is None else self._to_domain(model)

    async def find_by_user_and_provider(
        self,
        user_id: TSID,
        provider: IdentityProvider,
    ) -> UserIdentity | None:
        statement = select(UserIdentityModel).where(
            UserIdentityModel.user_id == user_id.value,
            UserIdentityModel.provider == provider.value,
        )
        model = await self._session.scalar(statement)
        return None if model is None else self._to_domain(model)

    @staticmethod
    def _to_domain(model: UserIdentityModel) -> UserIdentity:
        return UserIdentity(
            id=TSID(model.id),
            user_id=TSID(model.user_id),
            provider=IdentityProvider(model.provider),
            provider_subject=model.provider_subject,
            provider_email=model.provider_email,
            created_at=model.created_at,
        )
