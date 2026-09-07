from md2blog.modules.identity.application.models.google_auth import (
    GoogleConnection,
    GoogleLoginResult,
    GoogleLoginStatus,
)
from md2blog.modules.identity.application.port.outbound.google_identity import (
    GoogleIdentityClaims,
    GoogleIdentityVerifier,
    InvalidGoogleCredentialError,
)
from md2blog.modules.identity.application.port.outbound.security import Clock, PasswordHasher
from md2blog.modules.identity.domain.commands import (
    GoogleSignUpCommand,
    LinkGoogleAndLoginCommand,
)
from md2blog.modules.identity.domain.google_identity_policy import (
    GoogleIdentityAlreadyLinkedError,
    GoogleIdentityLinkPolicy,
    GoogleIdentityUnlinkPolicy,
)
from md2blog.modules.identity.domain.nickname_policy import NicknameUniquenessPolicy
from md2blog.modules.identity.domain.repositories import UserRepository
from md2blog.modules.identity.domain.user import AuthenticationFailedError, User
from md2blog.modules.identity.domain.user_identity import IdentityProvider, UserIdentity
from md2blog.modules.identity.domain.user_identity_repositories import UserIdentityRepository
from md2blog.modules.identity.domain.value_objects import Email
from md2blog.shared.domain.tsid import TSID


async def verified_claims(
    verifier: GoogleIdentityVerifier,
    credential: str,
) -> GoogleIdentityClaims:
    claims = await verifier.verify(credential)
    if not claims.email_verified:
        raise InvalidGoogleCredentialError
    return claims


class GoogleLogin:
    def __init__(
        self,
        users: UserRepository,
        identities: UserIdentityRepository,
        verifier: GoogleIdentityVerifier,
    ) -> None:
        self._users = users
        self._identities = identities
        self._verifier = verifier

    async def execute(self, credential: str) -> GoogleLoginResult:
        claims = await verified_claims(self._verifier, credential)
        email = Email(claims.email)
        identity = await self._identities.find_by_provider_subject(
            IdentityProvider.GOOGLE,
            claims.subject,
        )
        if identity is not None:
            user = await self._users.find_by_id(identity.user_id.value)
            if user is None:
                raise AuthenticationFailedError
            user.ensure_access_allowed()
            return GoogleLoginResult(GoogleLoginStatus.AUTHENTICATED, email, user)
        if await self._users.find_by_email(email) is not None:
            return GoogleLoginResult(GoogleLoginStatus.LINK_REQUIRED, email)
        return GoogleLoginResult(GoogleLoginStatus.SIGNUP_REQUIRED, email)


class GoogleSignUp:
    def __init__(
        self,
        users: UserRepository,
        identities: UserIdentityRepository,
        verifier: GoogleIdentityVerifier,
        nickname_policy: NicknameUniquenessPolicy,
        clock: Clock,
    ) -> None:
        self._users = users
        self._identities = identities
        self._verifier = verifier
        self._nickname_policy = nickname_policy
        self._clock = clock

    async def execute(self, command: GoogleSignUpCommand) -> User:
        claims = await verified_claims(self._verifier, command.credential)
        if await self._identities.find_by_provider_subject(
            IdentityProvider.GOOGLE, claims.subject
        ) is not None:
            raise GoogleIdentityAlreadyLinkedError
        email = Email(claims.email)
        if await self._users.find_by_email(email) is not None:
            raise GoogleAccountLinkRequiredError
        self._nickname_policy.ensure_available(
            is_already_used=await self._users.exists_by_display_name(command.display_name)
        )
        now = self._clock.now()
        user = User.sign_up_with_google(
            user_id=TSID.generate(),
            email=email,
            display_name=command.display_name,
            verified_at=now,
        )
        await self._users.add(user)
        await self._identities.add(
            UserIdentity(
                id=TSID.generate(),
                user_id=user.id,
                provider=IdentityProvider.GOOGLE,
                provider_subject=claims.subject,
                provider_email=email.value,
                created_at=now,
            )
        )
        return user


class LinkGoogleAndLogin:
    def __init__(
        self,
        users: UserRepository,
        identities: UserIdentityRepository,
        verifier: GoogleIdentityVerifier,
        password_hasher: PasswordHasher,
        clock: Clock,
    ) -> None:
        self._users = users
        self._identities = identities
        self._verifier = verifier
        self._password_hasher = password_hasher
        self._clock = clock

    async def execute(self, command: LinkGoogleAndLoginCommand) -> User:
        claims = await verified_claims(self._verifier, command.credential)
        if await self._identities.find_by_provider_subject(
            IdentityProvider.GOOGLE, claims.subject
        ) is not None:
            raise GoogleIdentityAlreadyLinkedError
        user = await self._users.find_by_email(Email(claims.email))
        if user is None or user.password_hash is None:
            raise AuthenticationFailedError
        user.authenticate(self._password_hasher.verify(command.password, user.password_hash))
        await self._identities.add(
            UserIdentity(
                id=TSID.generate(),
                user_id=user.id,
                provider=IdentityProvider.GOOGLE,
                provider_subject=claims.subject,
                provider_email=claims.email,
                created_at=self._clock.now(),
            )
        )
        return user


class ConnectGoogle:
    def __init__(
        self,
        identities: UserIdentityRepository,
        verifier: GoogleIdentityVerifier,
        clock: Clock,
        link_policy: GoogleIdentityLinkPolicy,
    ) -> None:
        self._identities = identities
        self._verifier = verifier
        self._clock = clock
        self._link_policy = link_policy

    async def execute(self, user: User, credential: str) -> None:
        claims = await verified_claims(self._verifier, credential)
        existing = await self._identities.find_by_provider_subject(
            IdentityProvider.GOOGLE, claims.subject
        )
        current_identity = await self._identities.find_by_user_and_provider(
            user.id, IdentityProvider.GOOGLE
        )
        self._link_policy.ensure_linkable(
            linked_to_another_user=existing is not None and existing.user_id != user.id,
            user_already_has_google=current_identity is not None,
        )
        await self._identities.add(
            UserIdentity(
                id=TSID.generate(),
                user_id=user.id,
                provider=IdentityProvider.GOOGLE,
                provider_subject=claims.subject,
                provider_email=claims.email,
                created_at=self._clock.now(),
            )
        )


class DisconnectGoogle:
    def __init__(
        self,
        identities: UserIdentityRepository,
        unlink_policy: GoogleIdentityUnlinkPolicy,
    ) -> None:
        self._identities = identities
        self._unlink_policy = unlink_policy

    async def execute(self, user: User) -> None:
        identity = await self._identities.find_by_user_and_provider(
            user.id, IdentityProvider.GOOGLE
        )
        self._unlink_policy.ensure_unlinkable(
            is_linked=identity is not None,
            has_password=user.has_password,
        )
        assert identity is not None
        await self._identities.delete(identity)


class GetGoogleConnection:
    def __init__(self, identities: UserIdentityRepository) -> None:
        self._identities = identities

    async def execute(self, user: User) -> GoogleConnection:
        identity = await self._identities.find_by_user_and_provider(
            user.id,
            IdentityProvider.GOOGLE,
        )
        return GoogleConnection(
            connected=identity is not None,
            email=identity.provider_email if identity else None,
            can_disconnect=identity is not None and user.has_password,
        )


class GoogleAccountLinkRequiredError(Exception):
    pass
