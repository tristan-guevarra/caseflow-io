# app settings - all loaded from env vars / .env file

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # general app stuff
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me"
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"

    # database connection strings
    DATABASE_URL: str = "postgresql+asyncpg://caseflow:caseflow_dev_2026@postgres:5432/caseflow"
    DATABASE_URL_SYNC: str = "postgresql://caseflow:caseflow_dev_2026@postgres:5432/caseflow"

    # redis for caching and celery
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # jwt auth config
    JWT_SECRET_KEY: str = "change-me-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # openai stuff for doc analysis
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # s3 / minio for file storage
    S3_ENDPOINT_URL: str = "http://minio:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "caseflow-documents"
    S3_REGION: str = "us-east-1"

    # rate limiting
    RATE_LIMIT_AI_REQUESTS_PER_MINUTE: int = 20
    RATE_LIMIT_API_REQUESTS_PER_MINUTE: int = 120

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


# cache settings so we only load once
@lru_cache()
def get_settings() -> Settings:
    return Settings()
