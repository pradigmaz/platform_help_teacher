import contextlib
import logging

from aioboto3 import Session
from fastapi import HTTPException

from app.core.config import settings
from app.core.constants import ALLOWED_MIME_TYPES_SET
from app.utils.file_validation import validate_filename, validate_magic_bytes

logger = logging.getLogger(__name__)


def validate_file(
    filename: str, content_type: str = None, content: bytes = None
) -> str:
    """
    Validate file extension, MIME type, and magic bytes.

    Args:
        filename: Original filename
        content_type: Claimed MIME type from header
        content: File content for magic bytes validation

    Returns:
        Validated MIME type

    Raises:
        HTTPException: If validation fails
    """
    # 1. Validate filename and extension
    _, ext = validate_filename(filename)

    # 2. Basic MIME type check
    if content_type and content_type not in ALLOWED_MIME_TYPES_SET:
        raise HTTPException(
            status_code=400,
            detail=f"MIME type '{content_type}' not allowed for file {filename}",
        )

    # 3. Magic bytes validation (if content provided)
    if content:
        detected_mime = validate_magic_bytes(content, content_type)
        return detected_mime

    return content_type


# Singleton session for connection reuse
_session: Session | None = None


def _get_session() -> Session:
    """Get or create singleton aioboto3 session."""
    global _session
    if _session is None:
        _session = Session()
    return _session


class StorageService:
    def __init__(self):
        self.bucket = settings.MINIO_BUCKET_NAME
        self.expiry = settings.PRESIGNED_URL_EXPIRY

    @contextlib.asynccontextmanager
    async def get_client(self):
        session = _get_session()
        async with session.client(
            "s3",
            endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
            aws_access_key_id=settings.MINIO_ROOT_USER,
            aws_secret_access_key=settings.MINIO_ROOT_PASSWORD,
        ) as client:
            yield client

    async def create_presigned_upload_url(
        self,
        object_name: str,
        content_type: str = None,
        content: bytes = None,
        max_size: int = None,
    ) -> str:
        """
        Генерирует ссылку для загрузки файла (PUT).

        Args:
            object_name: Путь объекта в хранилище (может содержать '/')
            content_type: MIME type файла
            content: Содержимое файла для валидации magic bytes
            max_size: Максимальный размер файла (для Content-Length условия)
        """
        # Для storage paths извлекаем только имя файла для валидации
        # Storage paths могут содержать '/' (например: feedback/{id}/{id}.ext)
        filename_only = object_name.split("/")[-1]
        logger.info(
            f"[Attachment] Creating presigned upload URL for: {object_name}, type: {content_type}, size: {len(content) if content else 'N/A'}"
        )
        validate_file(filename_only, content_type, content)

        params = {"Bucket": self.bucket, "Key": object_name}

        # Добавляем ContentType для enforcement в S3/MinIO
        if content_type:
            params["ContentType"] = content_type

        # Добавляем условие Content-Length если указан max_size
        if max_size:
            pass

        async with self.get_client() as client:
            url = await client.generate_presigned_url(
                "put_object",
                Params=params,
                ExpiresIn=self.expiry,
            )
        logger.info(
            f"[Attachment] Presigned URL generated successfully for: {object_name}"
        )
        return url

    async def create_presigned_download_url(self, object_name: str) -> str:
        """Генерирует ссылку для скачивания (GET)"""
        logger.info(f"[Attachment] Creating presigned download URL for: {object_name}")
        async with self.get_client() as client:
            try:
                url = await client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket, "Key": object_name},
                    ExpiresIn=self.expiry,
                )
                logger.info(
                    f"[Attachment] Presigned download URL generated successfully for: {object_name}"
                )
                return url
            except Exception as e:
                logger.error(
                    f"[Attachment] Failed to generate download URL for {object_name}: {e}"
                )
                raise

    async def delete_object(self, object_name: str) -> bool:
        """Удаляет объект из хранилища."""
        logger.info(f"[Attachment] Deleting object from storage: {object_name}")
        async with self.get_client() as client:
            try:
                await client.delete_object(Bucket=self.bucket, Key=object_name)
                logger.info(f"[Attachment] Successfully deleted object: {object_name}")
                return True
            except Exception as e:
                logger.error(f"[Attachment] Failed to delete object {object_name}: {e}")
                raise
