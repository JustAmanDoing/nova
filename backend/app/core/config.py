from functools import lru_cache
from pathlib import Path
from typing import Annotated, Self

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NOVA_",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "Nova API"
    app_version: str = "0.45.0"
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

    @model_validator(mode="after")
    def validate_storage_boundaries(self) -> Self:
        directories = {
            "intake": self.intake_path.resolve(),
            "library": (
                self.library_path or self.intake_path.parent / "library"
            ).resolve(),
            "backup": self.backup_path.resolve(),
        }
        directory_items = list(directories.items())
        for index, (left_name, left_path) in enumerate(directory_items):
            for right_name, right_path in directory_items[index + 1 :]:
                if (
                    left_path == right_path
                    or left_path.is_relative_to(right_path)
                    or right_path.is_relative_to(left_path)
                ):
                    raise ValueError(
                        "Nova storage directories must not overlap: "
                        f"{left_name} and {right_name}."
                    )

        database_path = self.database_path.resolve()
        for directory_name, directory_path in directory_items:
            if database_path == directory_path or database_path.is_relative_to(
                directory_path
            ):
                raise ValueError(
                    "The Nova database must remain outside the "
                    f"{directory_name} directory."
                )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
