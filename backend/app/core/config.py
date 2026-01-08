import os
from typing import Optional, List, Union
from pydantic import field_validator, PostgresDsn, computed_field, AnyHttpUrl, Field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[".env", "../deploy/.env"],
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True
    )

    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Edu Platform API"
    
    # URLS
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"] # Default safe

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]], info) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        return v
    
    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_production(cls, v: List[str], info) -> List[str]:
        # В продакшене нельзя использовать '*'
        env = os.getenv("ENVIRONMENT", "development")
        if env == "production":
            if "*" in v:
                 raise ValueError("Wildcard CORS (*) is not allowed in production!")
        return v

    # SECURITY
    SECRET_KEY: str = Field(..., repr=False)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 1 week

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY is too short! Use 'openssl rand -hex 32'")
        if v in ["changeme", "dev_secret", "secret"]:
             raise ValueError("Default SECRET_KEY is not allowed!")
        return v

    # DATABASE
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = Field(..., repr=False)
    POSTGRES_DB: str = "edu_platform"

    @computed_field(repr=False)
    def DATABASE_URL(self) -> str:
        return str(
            MultiHostUrl.build(
                scheme="postgresql+asyncpg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_SERVER,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
        )

    # AUTO-ADMIN SEEDING
    FIRST_SUPERUSER_ID: Optional[int] = None
    FIRST_SUPERUSER_USERNAME: str = "admin"

    # TELEGRAM
    TELEGRAM_BOT_TOKEN: str = Field(..., repr=False)
    TELEGRAM_WEBHOOK_SECRET: str = Field(..., repr=False)
    TELEGRAM_WEBHOOK_URL: Optional[str] = None

    # VK (Long Poll - не требует внешнего URL)
    VK_BOT_TOKEN: Optional[str] = Field(default=None, repr=False)
    VK_GROUP_ID: Optional[int] = None

    # REDIS
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_PASSWORD: Optional[str] = Field(default=None, repr=False)
    REDIS_SSL: bool = False 
    
    # MinIO (S3)
    MINIO_ENDPOINT: str = "minio:9000" 
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str = Field(..., repr=False)
    MINIO_BUCKET_NAME: str = "edu-uploads"
    PRESIGNED_URL_EXPIRY: int = 300 # 5 minutes

    # Import Settings
    MAX_STUDENTS_COUNT: int = 150
    MAX_IMPORT_FILE_SIZE: int = 5 * 1024 * 1024  # 5MB
    MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_PIN_ATTEMPTS: int = 5
    NAME_SANITIZATION_REGEX: str = r'[\d\.\,\;\t]'

    # Attestation Defaults
    ATTESTATION_DEFAULT_LABS_WEIGHT: float = 60.0
    ATTESTATION_DEFAULT_ATTENDANCE_WEIGHT: float = 20.0
    ATTESTATION_DEFAULT_ACTIVITY_WEIGHT: float = 20.0
    ATTESTATION_DEFAULT_REQUIRED_LABS_COUNT: int = 5
    ATTESTATION_DEFAULT_BONUS_PER_EXTRA_LAB: float = 0.4
    ATTESTATION_DEFAULT_SOFT_DEADLINE_PENALTY: float = 0.7
    ATTESTATION_DEFAULT_HARD_DEADLINE_PENALTY: float = 0.5
    ATTESTATION_DEFAULT_SOFT_DEADLINE_DAYS: int = 7
    ATTESTATION_DEFAULT_PRESENT_POINTS: float = 1.0
    ATTESTATION_DEFAULT_LATE_POINTS: float = 0.5
    ATTESTATION_DEFAULT_EXCUSED_POINTS: float = 0.0
    ATTESTATION_DEFAULT_ABSENT_POINTS: float = -0.1
    ATTESTATION_DEFAULT_ACTIVITY_ENABLED: bool = True
    ATTESTATION_DEFAULT_PARTICIPATION_POINTS: float = 0.5

    # Backup Settings
    BACKUP_ENCRYPTION_KEY: str = Field(default="", repr=False)
    BACKUP_STORAGE_BUCKET: str = "edu-backups"
    BACKUP_RETENTION_DAYS: int = 30

    @field_validator("BACKUP_ENCRYPTION_KEY")
    @classmethod
    def validate_backup_key(cls, v: str) -> str:
        # Allow empty in dev, require in production
        if v and len(v) < 32:
            raise ValueError("BACKUP_ENCRYPTION_KEY must be at least 32 characters")
        return v

settings = Settings()
