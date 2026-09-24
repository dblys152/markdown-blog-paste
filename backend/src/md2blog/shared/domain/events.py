from dataclasses import dataclass
from datetime import datetime

from md2blog.shared.domain.tsid import TSID


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    event_id: TSID
    aggregate_id: TSID
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return type(self).__name__
