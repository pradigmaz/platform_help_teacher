"""
Root conftest — sets required env vars BEFORE any app module is imported.
Must be in backend/ root so pytest loads it first.
"""
import os

os.environ.setdefault("POSTGRES_SERVER", "localhost")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("ENVIRONMENT", "test")
