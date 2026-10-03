from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class StoredObject:
    key: str
    last_modified: datetime


class ObjectStorage(Protocol):
    async def put(self, key: str, data: bytes, content_type: str) -> None: ...

    async def delete(self, key: str) -> None: ...

    async def get(self, key: str) -> bytes: ...

    async def create_download_url(self, key: str, *, expires_seconds: int) -> str: ...

    async def list(self, prefix: str) -> list[StoredObject]: ...
