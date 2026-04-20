from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from motoscrap import __version__


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
        default="postgresql+asyncpg://motoscrap:motoscrap@localhost:5432/motoscrap",
        alias="DATABASE_URL",
    )
    api_key: str | None = Field(default=None, alias="MOTOSCRAP_API_KEY")

    http_user_agent: str = Field(
        default=f"motoscrap/{__version__} (+https://github.com/kemalasliyuksek/motoscrap)",
        alias="HTTP_USER_AGENT",
    )
    http_rate_limit_per_sec: float = Field(default=1.0, alias="HTTP_RATE_LIMIT_PER_SEC")
    http_timeout_seconds: float = Field(default=20.0, alias="HTTP_TIMEOUT_SECONDS")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def api_key_normalized(self) -> str | None:
        if self.api_key is None:
            return None
        key = self.api_key.strip()
        return key or None


@lru_cache
def get_settings() -> Settings:
    return Settings()
