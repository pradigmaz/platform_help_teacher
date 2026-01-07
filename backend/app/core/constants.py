
# File Validation Constants

# Dictionary mapping MIME types to their standard file extensions.
# This serves as the single source of truth for allowed file uploads.
ALLOWED_UPLOAD_MIME_TYPES = {
    # Documents
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-excel": ".xls",
    "text/plain": ".txt",
    "text/csv": ".csv",
    "text/markdown": ".md",
    
    # Images
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    
    # Archives
    "application/zip": ".zip",
}

# Derived sets for validation
ALLOWED_MIME_TYPES_SET = set(ALLOWED_UPLOAD_MIME_TYPES.keys())
ALLOWED_EXTENSIONS_SET = set(ALLOWED_UPLOAD_MIME_TYPES.values())

# Telegram Security
TELEGRAM_SUBNETS = [
    "149.154.160.0/20",
    "91.108.4.0/22"
]

# Lecture Constants
LECTURE_PUBLIC_CODE_LENGTH = 8
LECTURE_PUBLIC_CODE_MAX_ATTEMPTS = 10
LECTURE_PDF_TIMEOUT_MS = 10000
LECTURE_PDF_RENDER_DELAY_MS = 2000
LECTURE_VISUALIZATION_TIMEOUT_MS = 5000
LECTURE_MAX_IMAGES_RESPONSE = 50

# Lab Constants
LAB_PUBLIC_CODE_LENGTH = 8
LAB_PUBLIC_CODE_MAX_ATTEMPTS = 10
LAB_CONTENT_MAX_SIZE_BYTES = 5_000_000  # 5MB
LAB_MAX_VARIANTS = 100
LAB_MAX_QUESTIONS = 50

# Rate Limiting
RATE_LIMIT_LAB_CREATE = "15/minute"
RATE_LIMIT_LAB_DELETE = "10/minute"
RATE_LIMIT_LAB_PUBLISH = "10/minute"

