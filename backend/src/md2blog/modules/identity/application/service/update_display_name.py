from md2blog.modules.identity.domain.commands import UpdateDisplayNameCommand
from md2blog.modules.identity.domain.nickname_policy import NicknameUniquenessPolicy
from md2blog.modules.identity.domain.repositories import UserRepository
from md2blog.modules.identity.domain.user import User


class UpdateDisplayName:
    def __init__(
        self,
        users: UserRepository,
        nickname_policy: NicknameUniquenessPolicy,
    ) -> None:
        self._users = users
        self._nickname_policy = nickname_policy

    async def execute(
        self,
        user: User,
        command: UpdateDisplayNameCommand,
    ) -> User:
        updated_user = user.change_display_name(command.display_name)
        if updated_user == user:
            return user
        self._nickname_policy.ensure_available(
            is_already_used=await self._users.exists_by_display_name(
                command.display_name,
                exclude_user_id=user.id,
            )
        )
        await self._users.save(updated_user)
        return updated_user
