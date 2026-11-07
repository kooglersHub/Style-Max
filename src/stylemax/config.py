from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="STYLEMAX_", extra="ignore")

    data_dir: Path = Path("data")
    frontend_dir: Path = Path("frontend/dist")
    secure_cookies: bool = False
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:7b"
    image_worker_url: str = ""
    image_worker_key: str = ""
    image_timeout: int = Field(default=600, ge=10, le=1800)
    ebay_client_id: str = ""
    ebay_client_secret: str = ""
    enable_kleinanzeigen: bool = False
    enable_vinted: bool = False
    marketplace_timeout: int = Field(default=20, ge=2, le=60)
    max_photo_bytes: int = 10 * 1024 * 1024


def get_settings():
    return Settings()
