from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    gemini_api_key: str = ""
    hf_token: str = ""
    gemini_model: str = "gemini-2.5-flash"
    hf_image_model: str = "black-forest-labs/FLUX.1-schnell"
    image_provider: str = "placeholder"
    panel_count: int = 5
    app_host: str = "127.0.0.1"
    app_port: int = 8000

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def templates_dir(self) -> Path:
        return BASE_DIR / "templates"

    @property
    def static_dir(self) -> Path:
        return BASE_DIR / "static"

@lru_cache
def get_settings() -> Settings:
    return Settings()
