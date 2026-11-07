"""Runtime configuration loaded from the environment."""

from functools import lru_cache
import os
import tempfile

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_temp_dir() -> str:
    return os.path.join(tempfile.gettempdir(), "lumina-ai")


class Settings(BaseSettings):
    """Deploy-time settings. Secrets do not belong in this service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "LUMINA AI"
    version: str = "1.1.0"
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    max_upload_bytes: int = Field(default=10 * 1024 * 1024, ge=1024)
    max_image_pixels: int = Field(default=24_000_000, ge=64)
    temp_dir: str = Field(default_factory=_default_temp_dir)
    jpeg_quality: int = Field(default=92, ge=70, le=95)
    zerodce_weights: str = ""
    zerodce_scale: int = Field(default=12, ge=1, le=32)
    max_inference_side: int = Field(default=1280, ge=64, le=4096)


@lru_cache
def get_settings() -> Settings:
    return Settings()
