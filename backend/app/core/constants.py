
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

