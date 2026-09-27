from dataclasses import dataclass
from typing import Protocol

from md2blog.modules.identity.domain.value_objects import Email


@dataclass(frozen=True, slots=True)
class OutboundEmail:
    to: Email
    subject: str
    html: str


class EmailSender(Protocol):
    async def send(self, message: OutboundEmail) -> None: ...


class EmailDeliveryError(Exception):
    def __init__(self, reason: str, provider_code: int | None = None) -> None:
        self.reason = reason
        self.provider_code = provider_code
        detail = f"reason={reason}"
        if provider_code is not None:
            detail = f"{detail}, provider_code={provider_code}"
        super().__init__(f"email delivery failed: {detail}")
