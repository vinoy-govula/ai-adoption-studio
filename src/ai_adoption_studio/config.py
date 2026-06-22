from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="STUDIO_", env_file=".env", extra="ignore")

    data_root: Path = Path("data")
    internal_api_key: str = "dev-key"
    eoi_rate_limit_per_minute: int = 30

    platform_api_key: str = ""
    gateway_base_url: str = "http://localhost:8000"
    runtime_manager_base_url: str = "http://localhost:8001"
    control_centre_base_url: str = "http://localhost:8002"
    delivery_validator_root: Path = Path("../ai-delivery-validator")

    cursor_api_key: str = ""
    cursor_workspace_root: Path = Path("..")
    cursor_model: str = "composer-2.5"

    local_llm_base_url: str = ""

    @property
    def eoi_question_set_path(self) -> Path:
        return Path(__file__).resolve().parents[2] / "docs" / "eoi-question-set-v1.json"

    @property
    def internal_question_set_path(self) -> Path:
        return (
            Path(__file__).resolve().parents[2]
            / "docs"
            / "assessment-question-set-internal-v1.json"
        )


settings = Settings()
