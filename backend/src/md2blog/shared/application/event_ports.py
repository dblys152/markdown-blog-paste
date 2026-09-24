from typing import Protocol

from md2blog.shared.application.event_records import OutboxMessage, SecurityAuditLog


class OutboxMessageRepository(Protocol):
    async def add(self, message: OutboxMessage) -> None: ...


class SecurityAuditLogRepository(Protocol):
    async def add(self, log: SecurityAuditLog) -> None: ...


class SensitiveValueCipher(Protocol):
    def encrypt(self, value: str) -> str: ...

    def decrypt(self, encrypted_value: str) -> str: ...
