from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from md2blog.modules.identity.domain.user import User, UserStatus
from md2blog.modules.identity.domain.value_objects import DisplayName, Email, PasswordHash
from md2blog.modules.identity.infrastructure.models import UserModel
from md2blog.shared.domain.tsid import TSID


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def exists_by_email(self, email: Email) -> bool:
        statement = select(exists().where(UserModel.email == email.value))
        return bool(await self._session.scalar(statement))

    async def exists_by_display_name(
        self,
        display_name: DisplayName,
        *,
        exclude_user_id: TSID | None = None,
    ) -> bool:
        conditions = [func.lower(UserModel.display_name) == display_name.value.lower()]
        if exclude_user_id is not None:
            conditions.append(UserModel.id != exclude_user_id.value)
        statement = select(exists().where(*conditions))
        return bool(await self._session.scalar(statement))

    async def add(self, user: User) -> None:
        self._session.add(
            UserModel(
                id=user.id.value,
                email=user.email.value,
                password_hash=user.password_hash.value if user.password_hash else None,
                display_name=user.display_name.value,
                email_verified_at=user.email_verified_at,
                status=user.status.value,
            )
        )
        await self._session.flush()

    async def save(self, user: User) -> None:
        model = await self._session.get(UserModel, user.id.value)
        if model is None:
            raise LookupError("user not found")
        model.display_name = user.display_name.value
        model.email_verified_at = user.email_verified_at
        model.password_hash = user.password_hash.value if user.password_hash else None
        model.status = user.status.value
        await self._session.flush()

    async def delete(self, user: User) -> None:
        model = await self._session.get(UserModel, user.id.value)
        if model is None:
            raise LookupError("user not found")
        await self._session.delete(model)
        await self._session.flush()

    async def find_by_id(self, user_id: int) -> User | None:
        model = await self._session.get(UserModel, user_id)
        return None if model is None else self._to_domain(model)

    async def find_by_email(self, email: Email) -> User | None:
        statement = select(UserModel).where(UserModel.email == email.value)
        model = await self._session.scalar(statement)
        return None if model is None else self._to_domain(model)

    @staticmethod
    def _to_domain(model: UserModel) -> User:
        return User(
            id=TSID(model.id),
            email=Email(model.email),
            password_hash=PasswordHash(model.password_hash) if model.password_hash else None,
            display_name=DisplayName(model.display_name),
            email_verified_at=model.email_verified_at,
            status=UserStatus(model.status),
        )
