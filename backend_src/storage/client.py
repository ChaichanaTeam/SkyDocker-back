from typing import AsyncGenerator

import aioboto3
from botocore.config import Config

from backend_src.core.config import Settings
from .constants import PRESIGNED_TTL_SECONDS


_session = aioboto3.Session()
_config = Config(signature_version="s3v4", s3={"addressing_style": "path"})


def _client(endpoint_url: str | None):
    return _session.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=Settings.STORAGE_APP_KEY,
        aws_secret_access_key=Settings.STORAGE_APP_SECRET,
        region_name="us-east-1",
        config=_config,
    )


class Storage:
    def __init__(self, s3, signer) -> None:
        self._s3 = s3
        # Signs URLs for the public address, presigning makes no request
        self._signer = signer

    async def put_object(self, bucket: str, key: str, body: bytes, content_type: str) -> None:
        await self._s3.put_object(Bucket=bucket, Key=key, Body=body, ContentType=content_type)

    async def copy_object(self, source_bucket: str, source_key: str, bucket: str, key: str) -> None:
        await self._s3.copy_object(CopySource={"Bucket": source_bucket, "Key": source_key}, Bucket=bucket, Key=key)

    async def delete_objects(self, bucket: str, keys: list[str]) -> None:
        for key in keys:
            await self._s3.delete_object(Bucket=bucket, Key=key)

    async def presigned_get(self, bucket: str, key: str, expires: int = PRESIGNED_TTL_SECONDS) -> str:
        return await self._signer.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires
        )

    async def bucket_exists(self, bucket: str) -> bool:
        await self._s3.head_bucket(Bucket=bucket)
        return True


async def get_storage() -> AsyncGenerator[Storage, None]:
    async with _client(Settings.STORAGE_URL) as s3, _client(Settings.STORAGE_PUBLIC_URL) as signer:
        yield Storage(s3, signer)
