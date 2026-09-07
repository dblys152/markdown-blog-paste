from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from md2blog.shared.domain.tsid import TSID


class IdentityProvider(StrEnum):
    GOOGLE = "google"


@dataclass(frozen=True, slots=True)
class UserIdentity:
    id: TSID
    user_id: TSID
    provider: IdentityProvider
    provider_subject: str
    provider_email: str
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.provider_subject:
            raise ValueError("provider subject must not be empty")
