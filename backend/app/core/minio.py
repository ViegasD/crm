import io

import boto3
from botocore.client import Config

from app.core.config import settings

_client = None
_presign_client = None


def _build_client(endpoint: str):
    endpoint_url = (
        endpoint
        if endpoint.startswith(("http://", "https://"))
        else f"{'https' if settings.minio_use_ssl else 'http'}://{endpoint}"
    )
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=Config(signature_version="s3v4"),
    )


def get_minio_client():
    global _client
    if _client is None:
        _client = _build_client(settings.minio_endpoint)
    return _client


def get_minio_presign_client():
    global _presign_client
    if _presign_client is None:
        _presign_client = _build_client(settings.minio_public_endpoint or settings.minio_endpoint)
    return _presign_client


def ensure_bucket(bucket: str) -> None:
    client = get_minio_client()
    existing = [b["Name"] for b in client.list_buckets().get("Buckets", [])]
    if bucket not in existing:
        client.create_bucket(Bucket=bucket)


def upload_file(bucket: str, key: str, data: bytes, content_type: str) -> None:
    ensure_bucket(bucket)
    get_minio_client().put_object(
        Bucket=bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
    )


def generate_presigned_url(bucket: str, key: str, expires: int = 3600) -> str:
    return get_minio_presign_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires,
    )


def delete_object(bucket: str, key: str) -> None:
    get_minio_client().delete_object(Bucket=bucket, Key=key)


def read_file(bucket: str, key: str, max_bytes: int) -> bytes:
    from botocore.exceptions import ClientError
    try:
        response = get_minio_client().get_object(Bucket=bucket, Key=key)
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in {"NoSuchKey", "NoSuchBucket", "404"}:
            raise KeyError(key) from None
        raise
    body = response["Body"]
    try:
        if int(response.get("ContentLength", 0)) > max_bytes:
            raise ValueError("Media too large")
        content = body.read(max_bytes + 1)
        if len(content) > max_bytes:
            raise ValueError("Media too large")
        return content
    finally:
        body.close()
