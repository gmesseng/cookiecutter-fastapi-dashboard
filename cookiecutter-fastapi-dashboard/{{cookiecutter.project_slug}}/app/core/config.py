"""
Configuration centralisée via pydantic-settings.
L'app crashe au démarrage si une variable critique manque — jamais de fallback insecure.
"""
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.core.constants import (
    PROJECT_NAME,
    API_V1_STR,
    COMPANY_NAME,
    ACCESS_TOKEN_EXPIRATION_TIME,
    ANALYTICS_SCHEMA,
    TABLE_FACT_EXAMPLE,
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB,
    REDIS_TTL,
    REDIS_KEY_PREFIX,
    BACKEND_CORS_ORIGINS,
)
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="{{ cookiecutter.env_prefix }}",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = PROJECT_NAME
    API_V1_STR: str = API_V1_STR
    COMPANY_NAME: str = COMPANY_NAME

    # ── JWT ──────────────────────────────────────────────────────────
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = ACCESS_TOKEN_EXPIRATION_TIME

    # ── PostgreSQL ───────────────────────────────────────────────────
    SOURCE_POSTGRES_URI: str
    DEST_POSTGRES_URI: str

    TABLE_FACT_EXAMPLE: str = TABLE_FACT_EXAMPLE
    ANALYTICS_SCHEMA: str = ANALYTICS_SCHEMA

    # ── Redis ────────────────────────────────────────────────────────
    REDIS_HOST: str = REDIS_HOST
    REDIS_PORT: int = REDIS_PORT
    REDIS_DB: int = REDIS_DB
    REDIS_TTL: int = REDIS_TTL
    REDIS_KEY_PREFIX: str = REDIS_KEY_PREFIX

    # ── CORS ─────────────────────────────────────────────────────────
    BACKEND_CORS_ORIGINS: str = BACKEND_CORS_ORIGINS

    @staticmethod
    def _to_async_uri(uri: str) -> str:
        """Convertit l'URI psycopg2 en URI asyncpg pour SQLAlchemy async."""
        for prefix in ("postgresql://", "postgres://"):
            if uri.startswith(prefix):
                return "postgresql+asyncpg://" + uri[len(prefix):]
        return uri

    @property
    def SOURCE_POSTGRES_ASYNC_URI(self) -> str:
        return self._to_async_uri(self.SOURCE_POSTGRES_URI)

    @property
    def DEST_POSTGRES_ASYNC_URI(self) -> str:
        return self._to_async_uri(self.DEST_POSTGRES_URI)

    @property
    def T_FACT_EXAMPLE(self) -> str:
        return f"{self.ANALYTICS_SCHEMA}.{self.TABLE_FACT_EXAMPLE}"

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def cors_origins_list(self) -> list[str]:
        import json
        v = self.BACKEND_CORS_ORIGINS.strip()
        if not v:
            return []
        if v.startswith("["):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(o).strip() for o in parsed if str(o).strip()]
            except json.JSONDecodeError:
                pass
        return [o.strip() for o in v.split(",") if o.strip()]

    # ── Validation ───────────────────────────────────────────────────
    @field_validator("SECRET_KEY")
    @classmethod
    def _no_placeholder_secret(cls, v: str) -> str:
        if v.lower() in {
            "changethis", "change_me", "secret", "todo", "",
            "generate_a_secure_key_here_never_commit_the_real_one",
        }:
            raise ValueError("SECRET_KEY contient un placeholder insecure.")
        return v

    @field_validator("SOURCE_POSTGRES_URI", "DEST_POSTGRES_URI")
    @classmethod
    def _no_placeholder_pg(cls, v: str) -> str:
        if not v or v.lower() in {"changethis", "todo"}:
            raise ValueError("URI PostgreSQL invalide.")
        return v


settings = Settings()  # type: ignore[call-arg]
