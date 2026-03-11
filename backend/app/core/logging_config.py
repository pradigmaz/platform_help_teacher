import logging
from logging.config import dictConfig
from pathlib import Path

VALID_LOG_LEVELS = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def normalize_log_level(value: str | None, default: str = "INFO") -> str:
    if not value:
        return default

    normalized = value.strip().upper()
    return normalized if normalized in VALID_LOG_LEVELS else default


def configure_logging(log_level: str | None, log_dir: str = "/app/logs") -> None:
    level = normalize_log_level(log_level)
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": LOG_FORMAT,
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": level,
                    "formatter": "standard",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": level,
                    "formatter": "standard",
                    "filename": f"{log_dir}/app.log",
                    "maxBytes": 10 * 1024 * 1024,
                    "backupCount": 5,
                    "encoding": "utf-8",
                },
            },
            "root": {
                "handlers": ["console"],
                "level": level,
            },
            "loggers": {
                "app": {
                    "handlers": ["console", "file"],
                    "level": level,
                    "propagate": False,
                },
                "aiogram": {
                    "handlers": ["console", "file"],
                    "level": level,
                    "propagate": False,
                },
                "audit": {
                    "handlers": ["console", "file"],
                    "level": level,
                    "propagate": False,
                },
                "uvicorn": {
                    "handlers": ["console"],
                    "level": level,
                    "propagate": False,
                },
                "uvicorn.error": {
                    "handlers": ["console"],
                    "level": level,
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": ["console"],
                    "level": level,
                    "propagate": False,
                },
            },
        }
    )
    logging.captureWarnings(True)
