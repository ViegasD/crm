from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    secret_key: str = "change-me"
    debug: bool = False
    access_token_expire_minutes: int = 60 * 24  # 24h
    refresh_token_expire_days: int = 30

    # Database
    database_url: str = "postgresql+asyncpg://crm:crm@localhost:5432/crm"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_use_ssl: bool = False
    minio_bucket: str = "crm-media"

    # Meta (WhatsApp Cloud API) webhook
    meta_webhook_verify_token: str = "changeme-meta-verify"

    # Encryption (AES-256, base64-encoded 32 bytes)
    credential_encryption_key: str = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="

    # Evolution API
    evolution_api_url: str = "http://localhost:8080"
    evolution_api_key: str = "evolution-secret-key"

    # LiteLLM
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
