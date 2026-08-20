from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NCLEX Daily API"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    database_url: str = (
        "postgresql+psycopg://nclex:nclex_local_password@localhost:5432/nclex_daily"
    )
    cors_origins: str = "http://localhost:5173"
    supabase_url: str | None = None
    supabase_publishable_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def normalized_supabase_url(self) -> str | None:
        return self.supabase_url.rstrip("/") if self.supabase_url else None


@lru_cache
def get_settings() -> Settings:
    """Load and cache settings for the lifetime of the current API process."""
    return Settings()
