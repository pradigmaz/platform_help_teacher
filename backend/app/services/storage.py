import contextlib
import logging
from pathlib import Path
from aioboto3 import Session
from fastapi import HTTPException
from app.core.config import settings
from app.core.constants import ALLOWED_EXTENSIONS_SET, ALLOWED_MIME_TYPES_SET

logger = logging.getLogger(__name__)

def validate_file(filename: str, content_type: str = None) -> None:
    """Validate file extension and MIME type"""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS_SET:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' not allowed")
    if content_type and content_type not in ALLOWED_MIME_TYPES_SET:
        raise HTTPException(
            status_code=400,
            detail=f"MIME type '{content_type}' not allowed for file {filename}"
        )


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

    async def create_presigned_upload_url(self, object_name: str, content_type: str = None) -> str:
        """Генерирует ссылку для загрузки файла (PUT)"""
        validate_file(object_name, content_type)
        async with self.get_client() as client:
            url = await client.generate_presigned_url(
                "put_object",
                Params={"Bucket": self.bucket, "Key": object_name},
                ExpiresIn=self.expiry,
            )
        return url

    async def create_presigned_download_url(self, object_name: str) -> str:
        """Генерирует ссылку для скачивания (GET)"""
        async with self.get_client() as client:
            try:
                url = await client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket, "Key": object_name},
                    ExpiresIn=self.expiry,
                )
            except Exception as e:
                logger.error(f"Failed to generate download URL: {e}")
                return None
        return url