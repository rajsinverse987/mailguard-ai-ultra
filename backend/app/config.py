"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    app_env: Literal["development", "staging", "production", "test"] = "development"
    app_name: str = "MailGuard AI Ultra"
    app_base_url: str = "http://localhost:3000"
    api_base_url: str = "http://localhost:8000"

    # --- Security ---
    jwt_secret: str = "dev-only-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24
    aes_secret: str = "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="  # base64

    # --- Database ---
    database_url: str = (
        "postgresql+asyncpg://mailguard:mailguard@localhost:5432/mailguard"
    )
    redis_url: RedisDsn = Field(default="redis://localhost:6379/0")  # type: ignore[assignment]
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # --- AI ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_tts_model: str = "tts-1"
    google_tts_key: str | None = None

    # --- Gmail OAuth ---
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/accounts/gmail/callback"
    gmail_pubsub_topic: str = ""

    # --- Outlook OAuth ---
    ms_client_id: str = ""
    ms_client_secret: str = ""
    ms_tenant: str = "common"
    ms_redirect_uri: str = "http://localhost:8000/api/v1/accounts/outlook/callback"

    # --- WhatsApp ---
    whatsapp_provider: Literal["meta", "twilio"] = "meta"
    whatsapp_token: str = ""
    whatsapp_phone_id: str = ""
    whatsapp_business_account_id: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = ""

    # --- Vector DB ---
    chroma_persist_dir: str = "./chroma_data"
    embedding_dim: int = 1536

    # --- Telemetry ---
    sentry_dsn: str | None = None
    log_level: str = "INFO"

    @field_validator("aes_secret")
    @classmethod
    def _validate_aes_secret(cls, v: str) -> str:
        import base64

        try:
            decoded = base64.b64decode(v, validate=True)
        except Exception as exc:  # noqa: BLE001
            raise ValueError("AES_SECRET must be valid base64") from exc
        if len(decoded) not in (16, 24, 32):
            raise ValueError("AES_SECRET must decode to 16, 24, or 32 bytes")
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
