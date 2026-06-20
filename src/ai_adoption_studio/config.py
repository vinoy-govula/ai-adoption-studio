from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="STUDIO_", env_file=".env", extra="ignore")

    data_root: Path = Path("data")
    internal_api_key: str = "dev-key"
    eoi_rate_limit_per_minute: int = 30


settings = Settings()
