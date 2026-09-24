from sqlalchemy.ext.asyncio import AsyncSession

from md2blog.shared.application.event_records import OutboxMessage, SecurityAuditLog
from md2blog.shared.infrastructure.event_models import (
    OutboxMessageModel,
    SecurityAuditLogModel,
)


class SqlAlchemyOutboxMessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, message: OutboxMessage) -> None:
        self._session.add(
            OutboxMessageModel(
                id=message.id.value,
                event_id=message.event_id.value,
                event_type=message.event_type,
                aggregate_id=message.aggregate_id.value,
                payload=message.payload,
                status=message.status.value,
                retry_count=message.retry_count,
                available_at=message.available_at,
                occurred_at=message.occurred_at,
                locked_at=message.locked_at,
                processed_at=message.processed_at,
                last_error=message.last_error,
                created_at=message.occurred_at,
            )
        )


class SqlAlchemySecurityAuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, log: SecurityAuditLog) -> None:
        self._session.add(
            SecurityAuditLogModel(
                id=log.id.value,
                event_id=log.event_id.value,
                event_type=log.event_type,
                user_id=log.user_id.value,
                occurred_at=log.occurred_at,
                details=log.details,
                created_at=log.occurred_at,
            )
        )
