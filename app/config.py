"""Application settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    """Typed settings loaded from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
        default=f"sqlite:///{(ROOT_DIR / 'data' / 'bluechipwager.db').as_posix()}",
        alias="DATABASE_URL",
    )
    odds_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ODDS_API_KEY", "ODDS_API", "ODDSPAPI"),
    )
    cfbd_api_key: str | None = Field(default=None, alias="CFBD_API_KEY")
    auth_secret_key: str = Field(default="dev-change-me-use-long-random-string", alias="AUTH_SECRET_KEY")
    auth_cookie_name: str = Field(default="bcw_session", alias="AUTH_COOKIE_NAME")
    auth_token_max_age: int = Field(default=60 * 60 * 24 * 7, alias="AUTH_TOKEN_MAX_AGE")
    auth_free_username: str = Field(default="demo_free", alias="AUTH_FREE_USERNAME")
    auth_free_password: str = Field(default="demoFree123", alias="AUTH_FREE_PASSWORD")
    auth_pro_username: str = Field(default="demo_pro", alias="AUTH_PRO_USERNAME")
    auth_pro_password: str = Field(default="demoPro123", alias="AUTH_PRO_PASSWORD")
    auth_research_username: str = Field(default="demo_research", alias="AUTH_RESEARCH_USERNAME")
    auth_research_password: str = Field(default="demoResearch123", alias="AUTH_RESEARCH_PASSWORD")
    auth_admin_username: str = Field(default="admin", alias="AUTH_ADMIN_USERNAME")
    auth_admin_password: str = Field(default="admin123", alias="AUTH_ADMIN_PASSWORD")
    auth_demo_username: str | None = Field(default=None, alias="AUTH_DEMO_USERNAME")
    auth_demo_password: str | None = Field(default=None, alias="AUTH_DEMO_PASSWORD")
    environment: str = Field(default="dev", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    google_studio_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GOOGLE_STUDIO_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY"),
    )
    grok_api_key: str | None = Field(default=None, alias="GROK_API_KEY")
    data_dir: Path = Field(default=ROOT_DIR / "data")
    raw_data_dir: Path = Field(default=ROOT_DIR / "data" / "raw")

    # nflverse release assets
    nflverse_pbp_url: str = (
        "https://github.com/nflverse/nflverse-data/releases/download/"
        "pbp/play_by_play_{season}.parquet"
    )
    nflverse_schedules_url: str = (
        "https://github.com/nflverse/nflverse-data/releases/download/"
        "schedules/games.parquet"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
