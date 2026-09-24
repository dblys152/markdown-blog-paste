from md2blog.modules.identity.application.port.outbound.google_identity import (
    GoogleIdentityVerifier,
    InvalidGoogleCredentialError,
)
from md2blog.modules.identity.application.port.outbound.security import Clock, PasswordHasher
from md2blog.modules.identity.domain.commands import DeleteAccountCommand
from md2blog.modules.identity.domain.events import AccountDeleted
from md2blog.modules.identity.domain.repositories import UserRepository
from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.user_identity import IdentityProvider
from md2blog.modules.identity.domain.user_identity_repositories import UserIdentityRepository
from md2blog.shared.application.events import DomainEventPublisher
from md2blog.shared.domain.tsid import TSID


class DeleteAccount:
    def __init__(
        self,
        users: UserRepository,
        password_hasher: PasswordHasher,
        identities: UserIdentityRepository,
        google_verifier: GoogleIdentityVerifier | None,
        events: DomainEventPublisher,
        clock: Clock,
    ) -> None:
        self._users = users
        self._password_hasher = password_hasher
        self._identities = identities
        self._google_verifier = google_verifier
        self._events = events
        self._clock = clock

    async def execute(self, user: User, command: DeleteAccountCommand) -> None:
        if user.has_password:
            password_hash = user.password_hash
            assert password_hash is not None
            password_matches = command.password is not None and self._password_hasher.verify(
                command.password,
                password_hash,
            )
            user.confirm_account_deletion(password_matches)
        else:
            await self._confirm_google_account(user, command.google_credential)
        await self._users.delete(user)
        await self._events.publish(
            AccountDeleted(
                event_id=TSID.generate(),
                aggregate_id=user.id,
                occurred_at=self._clock.now(),
                user_id=user.id,
            )
        )

    async def _confirm_google_account(self, user: User, credential: str | None) -> None:
        if credential is None or self._google_verifier is None:
            raise InvalidGoogleCredentialError
        claims = await self._google_verifier.verify(credential)
        identity = await self._identities.find_by_user_and_provider(
            user.id,
            IdentityProvider.GOOGLE,
        )
        if (
            not claims.email_verified
            or identity is None
            or identity.provider_subject != claims.subject
        ):
            raise InvalidGoogleCredentialError
        user.confirm_account_deletion(password_matches=True)
