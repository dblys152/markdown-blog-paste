from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import DisplayName, Email, PasswordHash
from md2blog.modules.identity.infrastructure.models import UserModel
from md2blog.shared.domain.tsid import TSID


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def exists_by_email(self, email: Email) -> bool:
        statement = select(exists().where(UserModel.email == email.value))
        return bool(await self._session.scalar(statement))

    async def add(self, user: User) -> None:
        self._session.add(
            UserModel(
                id=user.id.value,
                email=user.email.value,
                password_hash=user.password_hash.value,
                display_name=user.display_name.value,
                email_verified_at=user.email_verified_at,
                status=user.status,
            )
        )
        await self._session.flush()

    async def find_by_id(self, user_id: int) -> User | None:
        model = await self._session.get(UserModel, user_id)
        if model is None:
            return None
        return User(
            id=TSID(model.id),
            email=Email(model.email),
            password_hash=PasswordHash(model.password_hash),
            display_name=DisplayName(model.display_name),
            email_verified_at=model.email_verified_at,
            status=model.status,
        )
