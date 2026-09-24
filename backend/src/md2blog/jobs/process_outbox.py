import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, or_, select

from md2blog.modules.identity.application.outbox_handlers import (
    EmailVerificationMessageHandler,
    PasswordResetMessageHandler,
)
from md2blog.modules.identity.infrastructure.email import GmailSmtpEmailSender
from md2blog.settings import get_settings
from md2blog.shared.application.event_records import OutboxMessageStatus
from md2blog.shared.application.outbox import OutboxMessageDispatcher
from md2blog.shared.infrastructure.database import get_session_factory
from md2blog.shared.infrastructure.event_models import OutboxMessageModel
from md2blog.shared.infrastructure.sensitive_value_cipher import (
    FernetSensitiveValueCipher,
)

MAX_RETRIES = 5
LOCK_TIMEOUT = timedelta(minutes=10)
BATCH_SIZE = 20


async def claim_messages(now: datetime) -> list[OutboxMessageModel]:
    async with get_session_factory()() as session, session.begin():
        result = await session.scalars(
            select(OutboxMessageModel)
            .where(
                or_(
                    and_(
                        OutboxMessageModel.status == OutboxMessageStatus.PENDING.value,
                        OutboxMessageModel.available_at <= now,
                    ),
                    and_(
                        OutboxMessageModel.status == OutboxMessageStatus.PROCESSING.value,
                        OutboxMessageModel.locked_at < now - LOCK_TIMEOUT,
                    ),
                )
            )
            .order_by(OutboxMessageModel.available_at, OutboxMessageModel.id)
            .limit(BATCH_SIZE)
            .with_for_update(skip_locked=True)
        )
        messages = list(result)
        for message in messages:
            message.status = OutboxMessageStatus.PROCESSING.value
            message.locked_at = now
        return messages


def build_dispatcher() -> OutboxMessageDispatcher:
    settings = get_settings()
    if not settings.smtp_username or not settings.smtp_password or not settings.email_from:
        raise RuntimeError("SMTP configuration is incomplete")
    sender = GmailSmtpEmailSender(
        host=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password.get_secret_value(),
        from_address=settings.email_from,
    )
    cipher = FernetSensitiveValueCipher(settings.outbox_token_encryption_key.get_secret_value())
    dispatcher = OutboxMessageDispatcher()
    dispatcher.register(
        "EmailVerificationRequested",
        EmailVerificationMessageHandler(sender, cipher),
    )
    dispatcher.register(
        "PasswordResetRequested",
        PasswordResetMessageHandler(sender, cipher),
    )
    return dispatcher


async def process_message(message: OutboxMessageModel, dispatcher: OutboxMessageDispatcher) -> None:
    await dispatcher.dispatch(message.event_type, message.payload)


async def mark_completed(message_id: int, now: datetime) -> None:
    async with get_session_factory()() as session, session.begin():
        message = await session.get(OutboxMessageModel, message_id, with_for_update=True)
        if message is None:
            return
        complete_message(message, now)


def complete_message(message: OutboxMessageModel, now: datetime) -> None:
    message.status = OutboxMessageStatus.COMPLETED.value
    message.processed_at = now
    message.locked_at = None
    message.last_error = None


async def mark_failed(message_id: int, error: Exception, now: datetime) -> None:
    async with get_session_factory()() as session, session.begin():
        message = await session.get(OutboxMessageModel, message_id, with_for_update=True)
        if message is None:
            return
        message.retry_count += 1
        message.status = (
            OutboxMessageStatus.FAILED.value
            if message.retry_count >= MAX_RETRIES
            else OutboxMessageStatus.PENDING.value
        )
        message.available_at = now + timedelta(minutes=2 ** (message.retry_count - 1))
        message.locked_at = None
        message.last_error = str(error)[:2000]


async def run() -> None:
    dispatcher = build_dispatcher()
    messages = await claim_messages(datetime.now(UTC))
    for message in messages:
        try:
            await process_message(message, dispatcher)
        except Exception as error:
            await mark_failed(message.id, error, datetime.now(UTC))
        else:
            await mark_completed(message.id, datetime.now(UTC))


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
