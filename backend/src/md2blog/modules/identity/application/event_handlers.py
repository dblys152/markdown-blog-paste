from html import escape

from md2blog.modules.identity.domain.events import (
    AccountDeleted,
    AllSessionsRevoked,
    AuthenticationFailed,
    AuthenticationSucceeded,
    EmailVerificationRequested,
    EmailVerified,
    PasswordResetCompleted,
    PasswordResetRequested,
    UserIdentityLinked,
    UserIdentityUnlinked,
)
from md2blog.shared.application.event_ports import (
    OutboxMessageRepository,
    SecurityAuditLogRepository,
    SensitiveValueCipher,
)
from md2blog.shared.application.event_records import (
    OutboxMessage,
    OutboxMessageStatus,
    SecurityAuditLog,
)
from md2blog.shared.domain.tsid import TSID

SecurityAuditEvent = (
    AuthenticationSucceeded
    | AuthenticationFailed
    | EmailVerified
    | PasswordResetCompleted
    | AllSessionsRevoked
    | UserIdentityLinked
    | UserIdentityUnlinked
    | AccountDeleted
)


class EmailVerificationRequestedHandler:
    def __init__(
        self,
        repository: OutboxMessageRepository,
        cipher: SensitiveValueCipher,
        frontend_url: str,
    ) -> None:
        self._repository = repository
        self._cipher = cipher
        self._frontend_url = frontend_url.rstrip("/")

    async def handle(self, event: EmailVerificationRequested) -> None:
        await _add_email_message(
            repository=self._repository,
            cipher=self._cipher,
            event=event,
            subject="[MD2Blog] 이메일을 인증해 주세요",
            introduction=(
                f"{escape(event.display_name.value)}님, "
                "MD2Blog 가입을 완료하려면 이메일을 인증해 주세요."
            ),
            action="이메일 인증하기",
            action_url=f"{self._frontend_url}/verify-email",
        )


class PasswordResetRequestedHandler:
    def __init__(
        self,
        repository: OutboxMessageRepository,
        cipher: SensitiveValueCipher,
        frontend_url: str,
    ) -> None:
        self._repository = repository
        self._cipher = cipher
        self._frontend_url = frontend_url.rstrip("/")

    async def handle(self, event: PasswordResetRequested) -> None:
        await _add_email_message(
            repository=self._repository,
            cipher=self._cipher,
            event=event,
            subject="[MD2Blog] 비밀번호를 재설정해 주세요",
            introduction=(
                f"{escape(event.display_name.value)}님, 요청하신 비밀번호 재설정 링크입니다."
            ),
            action="비밀번호 재설정하기",
            action_url=f"{self._frontend_url}/reset-password",
        )


class SecurityAuditLogHandler:
    def __init__(self, repository: SecurityAuditLogRepository) -> None:
        self._repository = repository

    async def handle(self, event: SecurityAuditEvent) -> None:
        details: dict[str, str] = {}
        if isinstance(event, (UserIdentityLinked, UserIdentityUnlinked)):
            details["provider"] = event.provider.value
        await self._repository.add(
            SecurityAuditLog(
                id=TSID.generate(),
                event_id=event.event_id,
                event_type=event.event_type,
                user_id=event.user_id,
                occurred_at=event.occurred_at,
                details=details,
            )
        )


async def _add_email_message(
    *,
    repository: OutboxMessageRepository,
    cipher: SensitiveValueCipher,
    event: EmailVerificationRequested | PasswordResetRequested,
    subject: str,
    introduction: str,
    action: str,
    action_url: str,
) -> None:
    payload = {
        "to": event.email.value,
        "subject": subject,
        "introduction_html": introduction,
        "action_label": action,
        "action_url": escape(action_url, quote=True),
        "encrypted_token": cipher.encrypt(event.raw_token),
    }
    await repository.add(
        OutboxMessage(
            id=TSID.generate(),
            event_id=event.event_id,
            event_type=event.event_type,
            aggregate_id=event.aggregate_id,
            payload=payload,
            status=OutboxMessageStatus.PENDING,
            retry_count=0,
            available_at=event.occurred_at,
            occurred_at=event.occurred_at,
        )
    )
