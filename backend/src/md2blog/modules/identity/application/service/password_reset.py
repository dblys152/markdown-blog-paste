from dataclasses import dataclass
from datetime import timedelta
from html import escape
from urllib.parse import quote

from md2blog.modules.identity.application.port.outbound.email import (
    EmailSender,
    OutboundEmail,
    PasswordResetTokenManager,
)
from md2blog.modules.identity.application.port.outbound.security import Clock, PasswordHasher
from md2blog.modules.identity.domain.commands import (
    ConfirmPasswordResetCommand,
    RequestPasswordResetCommand,
)
from md2blog.modules.identity.domain.password_reset import PasswordResetToken
from md2blog.modules.identity.domain.password_reset_repositories import (
    PasswordResetTokenRepository,
)
from md2blog.modules.identity.domain.repositories import UserRepository
from md2blog.modules.identity.domain.session_repositories import AuthSessionRepository
from md2blog.shared.domain.tsid import TSID


@dataclass(frozen=True, slots=True)
class PasswordResetPolicy:
    token_ttl: timedelta
    resend_cooldown: timedelta
    daily_limit: int


class RequestPasswordReset:
    def __init__(
        self,
        *,
        users: UserRepository,
        tokens: PasswordResetTokenRepository,
        token_manager: PasswordResetTokenManager,
        email_sender: EmailSender,
        clock: Clock,
        policy: PasswordResetPolicy,
        frontend_url: str,
    ) -> None:
        self._users = users
        self._tokens = tokens
        self._token_manager = token_manager
        self._email_sender = email_sender
        self._clock = clock
        self._policy = policy
        self._frontend_url = frontend_url.rstrip("/")

    async def execute(self, command: RequestPasswordResetCommand) -> None:
        user = await self._users.find_by_email(command.email)
        if user is None:
            return

        now = self._clock.now()
        latest = await self._tokens.find_latest_by_user_id(user.id)
        if latest is not None and latest.created_at + self._policy.resend_cooldown > now:
            return
        recent_request_count = await self._tokens.count_created_since(
            user.id,
            now - timedelta(days=1),
        )
        if recent_request_count >= self._policy.daily_limit:
            return

        if latest is not None and latest.is_active(now):
            await self._tokens.save(latest.revoke(now))

        generated = self._token_manager.generate()
        token = PasswordResetToken.issue(
            token_id=TSID.generate(),
            user_id=user.id,
            token_hash=generated.token_hash,
            issued_at=now,
            expires_at=now + self._policy.token_ttl,
        )
        await self._tokens.add(token)
        reset_url = f"{self._frontend_url}/reset-password?token={quote(generated.raw, safe='')}"
        await self._email_sender.send(
            OutboundEmail(
                to=user.email,
                subject="[MD2Blog] 비밀번호를 재설정해 주세요",
                html=self._build_html(user.display_name.value, reset_url),
            )
        )

    @staticmethod
    def _build_html(display_name: str, reset_url: str) -> str:
        return (
            f"<p>{escape(display_name)}님, 요청하신 비밀번호 재설정 링크입니다.</p>"
            f'<p><a href="{escape(reset_url, quote=True)}">비밀번호 재설정하기</a></p>'
            "<p>본인이 요청하지 않았다면 이 메일을 무시해 주세요.</p>"
        )


class ConfirmPasswordReset:
    def __init__(
        self,
        *,
        users: UserRepository,
        sessions: AuthSessionRepository,
        tokens: PasswordResetTokenRepository,
        token_manager: PasswordResetTokenManager,
        password_hasher: PasswordHasher,
        clock: Clock,
    ) -> None:
        self._users = users
        self._sessions = sessions
        self._tokens = tokens
        self._token_manager = token_manager
        self._password_hasher = password_hasher
        self._clock = clock

    async def execute(self, command: ConfirmPasswordResetCommand) -> None:
        token = await self._tokens.find_by_token_hash_for_update(
            self._token_manager.hash(command.token)
        )
        if token is None:
            raise InvalidPasswordResetTokenError

        now = self._clock.now()
        used_token = token.use(now)
        user = await self._users.find_by_id(token.user_id.value)
        if user is None:
            raise InvalidPasswordResetTokenError

        password_hash = self._password_hasher.hash(command.new_password)
        await self._users.save(user.reset_password(password_hash))
        await self._tokens.save(used_token)
        await self._sessions.revoke_all_by_user_id(user.id, now)


class InvalidPasswordResetTokenError(Exception):
    pass
