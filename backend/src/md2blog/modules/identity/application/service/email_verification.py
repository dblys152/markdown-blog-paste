from dataclasses import dataclass
from datetime import timedelta
from html import escape
from urllib.parse import quote

from md2blog.modules.identity.application.port.outbound.email import (
    EmailSender,
    EmailVerificationTokenManager,
    OutboundEmail,
)
from md2blog.modules.identity.application.port.outbound.security import Clock
from md2blog.modules.identity.domain.email_verification import EmailVerificationToken
from md2blog.modules.identity.domain.email_verification_repositories import (
    EmailVerificationTokenRepository,
)
from md2blog.modules.identity.domain.repositories import UserRepository
from md2blog.modules.identity.domain.user import User
from md2blog.shared.domain.tsid import TSID


@dataclass(frozen=True, slots=True)
class EmailVerificationPolicy:
    token_ttl: timedelta
    resend_cooldown: timedelta
    daily_limit: int


class IssueEmailVerification:
    def __init__(
        self,
        *,
        tokens: EmailVerificationTokenRepository,
        token_manager: EmailVerificationTokenManager,
        email_sender: EmailSender,
        clock: Clock,
        policy: EmailVerificationPolicy,
        frontend_url: str,
    ) -> None:
        self._tokens = tokens
        self._token_manager = token_manager
        self._email_sender = email_sender
        self._clock = clock
        self._policy = policy
        self._frontend_url = frontend_url.rstrip("/")

    async def execute(self, user: User) -> None:
        if user.is_email_verified:
            return

        now = self._clock.now()
        latest = await self._tokens.find_latest_by_user_id(user.id)
        if latest is not None and latest.created_at + self._policy.resend_cooldown > now:
            retry_after = latest.created_at + self._policy.resend_cooldown - now
            raise EmailVerificationCooldownError(max(1, int(retry_after.total_seconds())))

        since = now - timedelta(days=1)
        if await self._tokens.count_created_since(user.id, since) >= self._policy.daily_limit:
            raise EmailVerificationDailyLimitError

        if latest is not None and latest.is_active(now):
            await self._tokens.save(latest.revoke(now))

        generated = self._token_manager.generate()
        token = EmailVerificationToken.issue(
            token_id=TSID.generate(),
            user_id=user.id,
            token_hash=generated.token_hash,
            issued_at=now,
            expires_at=now + self._policy.token_ttl,
        )
        await self._tokens.add(token)
        verification_url = (
            f"{self._frontend_url}/verify-email?token={quote(generated.raw, safe='')}"
        )
        await self._email_sender.send(
            OutboundEmail(
                to=user.email,
                subject="[MD2Blog] 이메일을 인증해 주세요",
                html=self._build_html(user, verification_url),
            )
        )

    @staticmethod
    def _build_html(user: User, verification_url: str) -> str:
        display_name = escape(user.display_name.value)
        safe_url = escape(verification_url, quote=True)
        return (
            f"<p>{display_name}님, MD2Blog 가입을 완료하려면 이메일을 인증해 주세요.</p>"
            f'<p><a href="{safe_url}">이메일 인증하기</a></p>'
            "<p>본인이 요청하지 않았다면 이 메일을 무시해 주세요.</p>"
        )


class ConfirmEmailVerification:
    def __init__(
        self,
        *,
        users: UserRepository,
        tokens: EmailVerificationTokenRepository,
        token_manager: EmailVerificationTokenManager,
        clock: Clock,
    ) -> None:
        self._users = users
        self._tokens = tokens
        self._token_manager = token_manager
        self._clock = clock

    async def execute(self, raw_token: str) -> User:
        token_hash = self._token_manager.hash(raw_token)
        token = await self._tokens.find_by_token_hash_for_update(token_hash)
        if token is None:
            raise InvalidEmailVerificationTokenError

        now = self._clock.now()
        confirmed_token = token.confirm(now)
        user = await self._users.find_by_id(token.user_id.value)
        if user is None:
            raise InvalidEmailVerificationTokenError

        verified_user = user.verify_email(now)
        await self._tokens.save(confirmed_token)
        await self._users.save(verified_user)
        return verified_user


class EmailVerificationCooldownError(Exception):
    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__("email verification resend cooldown")


class EmailVerificationDailyLimitError(Exception):
    pass


class InvalidEmailVerificationTokenError(Exception):
    pass
