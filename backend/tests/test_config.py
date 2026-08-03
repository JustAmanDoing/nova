from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_storage_directories_must_not_overlap(tmp_path: Path) -> None:
    with pytest.raises(
        ValidationError,
        match="storage directories must not overlap: intake and library",
    ):
        Settings(
            intake_path=tmp_path / "intake",
            library_path=tmp_path / "intake" / "library",
            backup_path=tmp_path / "backups",
            database_path=tmp_path / "nova.db",
        )


def test_database_must_remain_outside_document_directories(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValidationError,
        match="database must remain outside the backup directory",
    ):
        Settings(
            intake_path=tmp_path / "intake",
            library_path=tmp_path / "library",
            backup_path=tmp_path / "backups",
            database_path=tmp_path / "backups" / "nova.db",
        )


def test_sibling_storage_paths_are_accepted(tmp_path: Path) -> None:
    settings = Settings(
        intake_path=tmp_path / "intake",
        library_path=tmp_path / "library",
        backup_path=tmp_path / "backups",
        database_path=tmp_path / "nova.db",
    )

    assert settings.intake_path == tmp_path / "intake"
    assert settings.library_path == tmp_path / "library"


def test_archive_must_not_overlap_other_storage(tmp_path: Path) -> None:
    with pytest.raises(
        ValidationError,
        match="storage directories must not overlap: knowledge and archive",
    ):
        Settings(
            intake_path=tmp_path / "intake",
            library_path=tmp_path / "library",
            backup_path=tmp_path / "backups",
            knowledge_path=tmp_path / "knowledge",
            archive_path=tmp_path / "knowledge" / "archive",
            database_path=tmp_path / "nova.db",
        )
