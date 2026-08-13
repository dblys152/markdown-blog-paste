from md2blog.modules.identity.application.port.outbound.security import AccessTokenDecoder
from md2blog.modules.identity.domain.repositories import UserRepository
from md2blog.modules.identity.domain.user import AccessNotAllowedError, User


class AuthenticationRequiredError(Exception):
    pass


class AuthenticateAccessToken:
    def __init__(self, decoder: AccessTokenDecoder, users: UserRepository) -> None:
        self._decoder = decoder
        self._users = users

    async def execute(self, token: str) -> User:
        user_id = self._decoder.decode_subject(token)
        user = await self._users.find_by_id(user_id.value)
        if user is None:
            raise AuthenticationRequiredError
        try:
            user.ensure_access_allowed()
        except AccessNotAllowedError as error:
            raise AuthenticationRequiredError from error
        return user
