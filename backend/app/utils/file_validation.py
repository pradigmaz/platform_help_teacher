"""
Утилиты валидации файлов: magic bytes, MIME types, расширения.
Security: Защита от file upload attacks.
"""
import logging
import magic
from pathlib import Path
from typing import Optional, Tuple
from fastapi import HTTPException

from app.core.constants import ALLOWED_EXTENSIONS_SET, ALLOWED_MIME_TYPES_SET
from app.core import error_messages as em

logger = logging.getLogger(__name__)

# Magic bytes signatures для критических типов
MAGIC_SIGNATURES = {
    b'%PDF': 'application/pdf',
    b'\x89PNG': 'image/png',
    b'\xff\xd8\xff': 'image/jpeg',
    b'GIF87a': 'image/gif',
    b'GIF89a': 'image/gif',
    b'PK\x03\x04': 'application/zip',  # ZIP, DOCX, XLSX
    b'RIFF': 'image/webp',  # WebP (RIFF....WEBP)
}

# Опасные расширения (никогда не разрешать)
DANGEROUS_EXTENSIONS = {
    '.php', '.php3', '.php4', '.php5', '.phtml',
    '.exe', '.dll', '.bat', '.cmd', '.sh', '.bash',
    '.js', '.jsx', '.ts', '.tsx',  # Серверный JS
    '.py', '.pyc', '.pyo',
    '.rb', '.pl', '.cgi',
    '.asp', '.aspx', '.jsp',
    '.htaccess', '.htpasswd',
}


def validate_magic_bytes(content: bytes, claimed_mime: Optional[str] = None) -> str:
    """
    Проверяет реальный тип файла по magic bytes.
    
    Args:
        content: Содержимое файла (минимум первые 8KB)
        claimed_mime: Заявленный MIME type (для сравнения)
    
    Returns:
        Реальный MIME type
    
    Raises:
        HTTPException: Если тип не разрешён или не совпадает с заявленным
    """
    if len(content) < 4:
        raise HTTPException(status_code=400, detail=em.FILE_TOO_SMALL)
    
    # Используем python-magic для определения типа
    try:
        detected_mime = magic.from_buffer(content[:8192], mime=True)
    except Exception as e:
        logger.warning(f"Magic detection failed: {e}")
        # Fallback на ручную проверку сигнатур
        detected_mime = _detect_by_signature(content)
    
    if not detected_mime:
        raise HTTPException(status_code=400, detail=em.COULD_NOT_DETERMINE_FILE_TYPE)
    
    # Проверяем, что тип разрешён
    if detected_mime not in ALLOWED_MIME_TYPES_SET:
        logger.warning(f"Blocked file upload: detected={detected_mime}, claimed={claimed_mime}")
        raise HTTPException(
            status_code=400,
            detail=em.format_error(em.FILE_TYPE_NOT_ALLOWED, type=detected_mime)
        )
    
    # Если заявлен MIME — проверяем совпадение
    if claimed_mime and claimed_mime != detected_mime:
        # Разрешаем некоторые эквиваленты
        if not _are_mime_equivalent(claimed_mime, detected_mime):
            logger.warning(
                f"MIME mismatch: claimed={claimed_mime}, detected={detected_mime}"
            )
            raise HTTPException(
                status_code=400,
                detail=em.FILE_CONTENT_MISMATCH
            )
    
    return detected_mime


def _detect_by_signature(content: bytes) -> Optional[str]:
    """Fallback определение типа по сигнатуре."""
    for signature, mime_type in MAGIC_SIGNATURES.items():
        if content.startswith(signature):
            return mime_type
    return None


def _are_mime_equivalent(mime1: str, mime2: str) -> bool:
    """Проверяет эквивалентность MIME типов."""
    equivalents = [
        {'image/jpeg', 'image/jpg'},
        {'application/zip', 'application/x-zip-compressed'},
        {'text/plain', 'text/x-python', 'text/x-script.python'},
    ]
    for group in equivalents:
        if mime1 in group and mime2 in group:
            return True
    return False


def validate_filename(filename: str) -> Tuple[str, str]:
    """
    Валидирует имя файла и возвращает безопасное расширение.
    
    Returns:
        Tuple[safe_name, extension]
    
    Raises:
        HTTPException: Если расширение опасное или не разрешено
    """
    if not filename:
        raise HTTPException(status_code=400, detail=em.FILENAME_REQUIRED)
    
    # Защита от path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(status_code=400, detail=em.INVALID_FILENAME)
    
    path = Path(filename)
    ext = path.suffix.lower()
    
    # Проверка на опасные расширения
    if ext in DANGEROUS_EXTENSIONS:
        logger.warning(f"Blocked dangerous file extension: {ext}")
        raise HTTPException(status_code=400, detail=em.format_error(em.FILE_TYPE_NOT_ALLOWED, type=ext))
    
    # Проверка на разрешённые расширения
    if ext not in ALLOWED_EXTENSIONS_SET:
        raise HTTPException(status_code=400, detail=em.format_error(em.FILE_TYPE_NOT_ALLOWED, type=ext))
    
    # Возвращаем безопасное имя (только basename)
    safe_name = path.name
    return safe_name, ext


def validate_file_upload(
    content: bytes,
    filename: str,
    claimed_mime: Optional[str] = None,
    max_size: Optional[int] = None
) -> Tuple[str, str]:
    """
    Полная валидация загружаемого файла.
    
    Args:
        content: Содержимое файла
        filename: Имя файла
        claimed_mime: Заявленный MIME type
        max_size: Максимальный размер в байтах
    
    Returns:
        Tuple[detected_mime, safe_extension]
    """
    # 1. Проверка размера
    if max_size and len(content) > max_size:
        max_mb = max_size // (1024*1024)
        raise HTTPException(
            status_code=400,
            detail=em.format_error(em.FILE_TOO_LARGE, max=f"{max_mb}MB")
        )
    
    # 2. Валидация имени файла
    _, ext = validate_filename(filename)
    
    # 3. Проверка magic bytes
    detected_mime = validate_magic_bytes(content, claimed_mime)
    
    return detected_mime, ext
