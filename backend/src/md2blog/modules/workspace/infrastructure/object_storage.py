import asyncio
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

import boto3  # type: ignore[import-untyped]

from md2blog.modules.workspace.application.port.outbound.object_storage import StoredObject
from md2blog.settings import Settings, get_settings


class FileSystemObjectStorage:
    def __init__(self, root: Path) -> None:
        self._root = root

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        path = self._path(key)
        await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_bytes, data)

    async def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            await asyncio.to_thread(path.unlink)

    async def get(self, key: str) -> bytes:
        return await asyncio.to_thread(self._path(key).read_bytes)

    async def create_download_url(self, key: str, *, expires_seconds: int) -> str:
        return f"local://{key}"

    async def list(self, prefix: str) -> list[StoredObject]:
        root = self._path(prefix)
        if not root.exists():
            return []
        paths = await asyncio.to_thread(lambda: list(root.rglob("*")))
        return [
            StoredObject(
                key=str(path.relative_to(self._root)),
                last_modified=datetime.fromtimestamp(path.stat().st_mtime, tz=UTC),
            )
            for path in paths
            if path.is_file()
        ]

    def _path(self, key: str) -> Path:
        path = (self._root / key).resolve()
        if self._root.resolve() not in path.parents:
            raise ValueError("invalid storage key")
        return path


class R2ObjectStorage:
    def __init__(
        self,
        *,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        bucket: str,
    ) -> None:
        self._bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
        )

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self._client.delete_object, Bucket=self._bucket, Key=key)

    async def get(self, key: str) -> bytes:
        response = await asyncio.to_thread(
            self._client.get_object, Bucket=self._bucket, Key=key
        )
        return await asyncio.to_thread(response["Body"].read)

    async def create_download_url(self, key: str, *, expires_seconds: int) -> str:
        return await asyncio.to_thread(
            self._client.generate_presigned_url,
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_seconds,
        )

    async def list(self, prefix: str) -> list[StoredObject]:
        def collect() -> list[StoredObject]:
            paginator = self._client.get_paginator("list_objects_v2")
            return [
                StoredObject(key=item["Key"], last_modified=item["LastModified"])
                for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix)
                for item in page.get("Contents", [])
            ]

        return await asyncio.to_thread(collect)


@lru_cache
def get_configured_object_storage() -> FileSystemObjectStorage | R2ObjectStorage:
    return build_object_storage(get_settings())


def build_object_storage(settings: Settings) -> FileSystemObjectStorage | R2ObjectStorage:
    if settings.object_storage_backend == "r2":
        if not all(
            [
                settings.r2_endpoint_url,
                settings.r2_access_key_id,
                settings.r2_secret_access_key,
                settings.r2_bucket,
            ]
        ):
            raise RuntimeError("R2 object storage settings are incomplete")
        return R2ObjectStorage(
            endpoint_url=settings.r2_endpoint_url or "",
            access_key_id=settings.r2_access_key_id or "",
            secret_access_key=(
                settings.r2_secret_access_key.get_secret_value()
                if settings.r2_secret_access_key
                else ""
            ),
            bucket=settings.r2_bucket or "",
        )
    return FileSystemObjectStorage(Path(settings.object_storage_local_root))
