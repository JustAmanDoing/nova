from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NOVA_",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "Nova API"
    app_version: str = "0.19.1"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    allowed_hosts: Annotated[list[str], NoDecode] = [
        "localhost",
        "127.0.0.1",
        "testserver",
    ]
    intake_path: Path = Path("data/intake")
    library_path: Path | None = None
    database_path: Path = Path("data/nova.db")
    backup_path: Path = Path("data/backups")
    intake_scan_seconds: float = 3.0
    action_stale_seconds: float = 300.0
    max_text_bytes: int = 1_000_000
    max_extracted_text_bytes: int = 1_000_000
    ocr_enabled: bool = True
    ocr_max_pages: int = Field(default=10, ge=1, le=100)
    ocr_timeout_seconds: float = Field(default=60.0, ge=1.0, le=600.0)
    ocr_max_render_dimension: int = Field(default=2400, ge=600, le=5000)
    ocr_max_rendered_bytes: int = Field(
        default=50_000_000,
        ge=1_000_000,
        le=500_000_000,
    )

    @field_validator("cors_origins", "allowed_hosts", mode="before")
    @classmethod
    def parse_csv_list(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
