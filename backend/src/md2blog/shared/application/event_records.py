from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from md2blog.shared.domain.tsid import TSID


class OutboxMessageStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class OutboxMessage:
    id: TSID
    event_id: TSID
    event_type: str
    aggregate_id: TSID
    payload: dict[str, str]
    status: OutboxMessageStatus
    retry_count: int
    available_at: datetime
    occurred_at: datetime
    locked_at: datetime | None = None
    processed_at: datetime | None = None
    last_error: str | None = None


@dataclass(frozen=True, slots=True)
class SecurityAuditLog:
    id: TSID
    event_id: TSID
    event_type: str
    user_id: TSID
    occurred_at: datetime
    details: dict[str, str]
