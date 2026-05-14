import io

import boto3
from botocore.client import Config

from app.core.config import settings

_client = None


def get_minio_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=f"{'https' if settings.minio_use_ssl else 'http'}://{settings.minio_endpoint}",
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            config=Config(signature_version="s3v4"),
        )
    return _client


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
    return get_minio_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires,
    )


def delete_object(bucket: str, key: str) -> None:
    get_minio_client().delete_object(Bucket=bucket, Key=key)
