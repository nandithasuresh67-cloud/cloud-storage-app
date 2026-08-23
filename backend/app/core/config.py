"""
Application configuration.

Values are loaded from environment variables / a local .env file
(see backend/.env.example). Nothing here is hardcoded so the same
code works across local, staging, and production environments.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "Cloud Storage Service API"
    ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    # --- Supabase ---
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = "files"

    # --- Database (Supabase Postgres connection string) ---
    # postgresql+psycopg2://postgres:<password>@<host>:5432/postgres
    DATABASE_URL: str = ""

    # --- Auth / JWT (wired up on Day 2 backend work) ---
    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- CORS ---
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # --- File upload validation (Day 3) ---
    MAX_UPLOAD_SIZE_MB: int = 100
    # Blocklist rather than allowlist: this is a general-purpose file store
    # (like Drive), so most mime types are fine. Block the categories most
    # likely to be executed/scripted if downloaded and run.
    BLOCKED_MIME_TYPES: list[str] = [
        "application/x-msdownload",
        "application/x-executable",
        "application/x-sh",
        "application/x-bat",
        "application/vnd.microsoft.portable-executable",
    ]
    SIGNED_URL_EXPIRES_IN_SECONDS: int = 3600

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
