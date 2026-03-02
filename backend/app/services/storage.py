# s3/minio storage service for uploading and downloading docs

import uuid
from io import BytesIO

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


# create an s3 client pointed at minio
def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
        config=Config(signature_version="s3v4"),
    )


# upload a file to s3 and return the storage path
# path format: {org_id}/{matter_id}/{uuid}_{filename}
def upload_document(
    file_content: bytes,
    filename: str,
    organization_id: str,
    matter_id: str,
    content_type: str = "application/octet-stream",
) -> str:
    s3 = get_s3_client()
    file_uuid = str(uuid.uuid4())
    safe_filename = filename.replace("/", "_").replace("\\", "_")
    storage_path = f"{organization_id}/{matter_id}/{file_uuid}_{safe_filename}"

    try:
        s3.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=storage_path,
            Body=file_content,
            ContentType=content_type,
        )
        logger.info("document_uploaded", storage_path=storage_path, size=len(file_content))
        return storage_path
    except ClientError as e:
        logger.error("s3_upload_failed", error=str(e), filename=filename)
        raise


# download a file from s3
def download_document(storage_path: str) -> bytes:
    s3 = get_s3_client()
    try:
        response = s3.get_object(Bucket=settings.S3_BUCKET_NAME, Key=storage_path)
        return response["Body"].read()
    except ClientError as e:
        logger.error("s3_download_failed", error=str(e), path=storage_path)
        raise


# delete a file from s3
def delete_document(storage_path: str) -> None:
    s3 = get_s3_client()
    try:
        s3.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=storage_path)
        logger.info("document_deleted", storage_path=storage_path)
    except ClientError as e:
        logger.error("s3_delete_failed", error=str(e), path=storage_path)
        raise


# get a temporary download link, defaults to 1 hour
def generate_presigned_url(storage_path: str, expires_in: int = 3600) -> str:
    s3 = get_s3_client()
    try:
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET_NAME, "Key": storage_path},
            ExpiresIn=expires_in,
        )
        return url
    except ClientError as e:
        logger.error("presigned_url_failed", error=str(e), path=storage_path)
        raise
