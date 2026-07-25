import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import LOCAL_ACTION_HEADER, LOCAL_ACTION_VALUE
from app.core.config import Settings
from app.main import create_app
from app.schemas.intake import ApprovalAction, ApprovalRequest
from app.schemas.learning import LearningResetRequest
from app.services.intake import IntakeService
from app.services.learning import (
    current_learning_revision,
    learned_destination,
    list_learning_preferences,
    record_confirmed_move,
    revert_confirmed_move,
)

LOCAL_ACTION_HEADERS = {LOCAL_ACTION_HEADER: LOCAL_ACTION_VALUE}


def _record(
    connection: sqlite3.Connection,
    operation: int,
    destination: str,
) -> None:
    record_confirmed_move(
        connection,
        operation_id=f"operation-{operation}",
        file_id=f"file-{operation}",
        source_sha256=f"hash-{operation}",
        document_type="plain_text",
        base_category="Financial",
        base_destination="Financial/Invoices",
        approved_category="Financial",
        approved_destination=destination,
        approved_filename=f"invoice-{operation}.txt",
        created_at=f"2026-07-25T00:00:0{operation}+00:00",
    )


def _write_invoice(path: Path, number: int) -> None:
    path.write_text(
        "Invoice\n"
        f"Invoice number: LEARN-{number}\n"
        "Invoice date: 25-07-2026\n"
        f"Supplier: S{number}\n"
        f"Total: ${number}.00 AUD",
        encoding="utf-8",
    )


def test_destination_learning_requires_three_examples_and_seventy_five_percent(
    tmp_path: Path,
) -> None:
    service = IntakeService(tmp_path / "intake", tmp_path / "nova.db")
    service.initialize()
    with closing(sqlite3.connect(service.database_path)) as connection:
        connection.row_factory = sqlite3.Row
        _record(connection, 1, "Financial/Preferred")
        _record(connection, 2, "Financial/Preferred")
        assert (
            learned_destination(
                connection,
                document_type="plain_text",
                base_category="Financial",
            )
            is None
        )

        _record(connection, 3, "Financial/Preferred")
        preference = learned_destination(
            connection,
            document_type="plain_text",
            base_category="Financial",
        )
        assert preference is not None
        assert preference.destination == "Financial/Preferred"
        assert preference.supporting_examples == 3
        assert preference.total_examples == 3
        assert preference.share == 1

        _record(connection, 4, "Financial/Other")
        assert (
            learned_destination(
                connection,
                document_type="plain_text",
                base_category="Financial",
            )
            is not None
        )
        _record(connection, 5, "Financial/Other")
        assert (
            learned_destination(
                connection,
                document_type="plain_text",
                base_category="Financial",
            )
            is None
        )


def test_undo_invalidates_learning_example_and_advances_revision(
    tmp_path: Path,
) -> None:
    service = IntakeService(tmp_path / "intake", tmp_path / "nova.db")
    service.initialize()
    with closing(sqlite3.connect(service.database_path)) as connection:
        connection.row_factory = sqlite3.Row
        _record(connection, 1, "Financial/Preferred")
        assert current_learning_revision(
            connection,
            document_type="plain_text",
            base_category="Financial",
        ) == 1

        revert_confirmed_move(
            connection,
            operation_id="operation-1",
            reverted_at="2026-07-25T01:00:00+00:00",
        )

        assert current_learning_revision(
            connection,
            document_type="plain_text",
            base_category="Financial",
        ) == 2
        assert (
            learned_destination(
                connection,
                document_type="plain_text",
                base_category="Financial",
            )
            is None
        )


def test_duplicate_operation_does_not_advance_learning_revision(
    tmp_path: Path,
) -> None:
    service = IntakeService(tmp_path / "intake", tmp_path / "nova.db")
    service.initialize()
    with closing(sqlite3.connect(service.database_path)) as connection:
        connection.row_factory = sqlite3.Row
        _record(connection, 1, "Financial/Preferred")
        _record(connection, 1, "Financial/Preferred")

        assert current_learning_revision(
            connection,
            document_type="plain_text",
            base_category="Financial",
        ) == 1
        count = connection.execute(
            "SELECT COUNT(*) FROM learning_examples"
        ).fetchone()[0]
        assert count == 1


def test_learning_preferences_include_active_and_reverted_examples(
    tmp_path: Path,
) -> None:
    service = IntakeService(tmp_path / "intake", tmp_path / "nova.db")
    service.initialize()
    with closing(sqlite3.connect(service.database_path)) as connection:
        connection.row_factory = sqlite3.Row
        _record(connection, 1, "Financial/Preferred")
        _record(connection, 2, "Financial/Preferred")
        _record(connection, 3, "Financial/Preferred")
        _record(connection, 4, "Financial/Other")

        preference = list_learning_preferences(connection)[0]
        assert preference.candidate_destination == "Financial/Preferred"
        assert preference.supporting_examples == 3
        assert preference.active_examples == 4
        assert preference.stored_examples == 4
        assert preference.share == 0.75
        assert preference.eligible is True

        revert_confirmed_move(
            connection,
            operation_id="operation-1",
            reverted_at="2026-07-25T01:00:00+00:00",
        )
        preference = list_learning_preferences(connection)[0]
        assert preference.supporting_examples == 2
        assert preference.active_examples == 3
        assert preference.stored_examples == 4
        assert preference.eligible is False


def test_category_correction_is_not_used_as_destination_learning(
    tmp_path: Path,
) -> None:
    service = IntakeService(
        intake_path=tmp_path / "intake",
        library_path=tmp_path / "library",
        database_path=tmp_path / "nova.db",
    )
    service.initialize()
    source = service.intake_path / "invoice-category-correction.txt"
    _write_invoice(source, 1)
    service.scan()
    record = next(
        item
        for item in service.list_files()
        if item.original_name == source.name
    )

    service.review_recommendation(
        record.id,
        ApprovalRequest(
            action=ApprovalAction.approve,
            category="Reference",
            destination="Reference/Invoices",
        ),
    )
    service.execute_approved(record.id)

    with closing(sqlite3.connect(service.database_path)) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM learning_examples"
        ).fetchone()[0]
        assert count == 0


def test_three_confirmed_moves_adjust_only_future_suggested_destination(
    tmp_path: Path,
) -> None:
    service = IntakeService(
        intake_path=tmp_path / "intake",
        library_path=tmp_path / "library",
        database_path=tmp_path / "nova.db",
    )
    service.initialize()
    moves = []
    learned_destination_path = "Preferred"

    for number in range(1, 4):
        source = service.intake_path / f"invoice-{number}.txt"
        _write_invoice(source, number)
        service.scan()
        record = next(
            item
            for item in service.list_files()
            if item.original_name == source.name
        )
        assert record.recommendation is not None
        service.review_recommendation(
            record.id,
            ApprovalRequest(
                action=ApprovalAction.approve,
                destination=learned_destination_path,
            ),
        )
        moves.append(service.execute_approved(record.id))

    fourth = service.intake_path / "invoice-4.txt"
    _write_invoice(fourth, 4)
    service.scan()
    recommendation = next(
        item.recommendation
        for item in service.list_files()
        if item.original_name == fourth.name
    )

    assert recommendation is not None
    assert recommendation.destination == learned_destination_path
    assert any(
        "3 of 3 active, confirmed moves" in reason
        for reason in recommendation.reasons
    )
    assert any(
        "still requires explicit approval" in reason
        for reason in recommendation.reasons
    )

    service.undo_action(moves[0].operation_id)
    refreshed = next(
        item.recommendation
        for item in service.list_files()
        if item.original_name == fourth.name
    )

    assert refreshed is not None
    assert refreshed.destination == "Financial/Invoices"
    assert all(
        "Learned the destination" not in reason
        for reason in refreshed.reasons
    )


def test_user_can_inspect_and_reset_stored_learning(
    tmp_path: Path,
) -> None:
    service = IntakeService(
        intake_path=tmp_path / "intake",
        library_path=tmp_path / "library",
        database_path=tmp_path / "nova.db",
    )
    service.initialize()
    destination = "Preferred"
    for number in range(1, 4):
        source = service.intake_path / f"invoice-reset-{number}.txt"
        _write_invoice(source, number)
        service.scan()
        record = next(
            item
            for item in service.list_files()
            if item.original_name == source.name
        )
        service.review_recommendation(
            record.id,
            ApprovalRequest(
                action=ApprovalAction.approve,
                destination=destination,
            ),
        )
        service.execute_approved(record.id)

    fourth = service.intake_path / "invoice-reset-4.txt"
    _write_invoice(fourth, 4)
    service.scan()
    preference = service.learning_preferences()[0]
    assert preference.candidate_destination == destination
    assert preference.eligible is True

    with pytest.raises(ValueError, match="confirmation did not match"):
        service.reset_learning(
            LearningResetRequest(
                document_type="plain_text",
                base_category="Financial",
                confirmation="FORGET",
            )
        )

    result = service.reset_learning(
        LearningResetRequest(
            document_type="plain_text",
            base_category="Financial",
            confirmation="FORGET plain_text / Financial",
        )
    )
    assert result.removed_examples == 3
    assert service.learning_preferences() == []
    refreshed = next(
        item.recommendation
        for item in service.list_files()
        if item.original_name == fourth.name
    )
    assert refreshed is not None
    assert refreshed.destination == "Financial/Invoices"

    with closing(sqlite3.connect(service.database_path)) as connection:
        examples = connection.execute(
            "SELECT COUNT(*) FROM learning_examples"
        ).fetchone()[0]
        event = connection.execute(
            """
            SELECT kind, removed_examples
            FROM learning_events
            """
        ).fetchone()
    assert examples == 0
    assert event == ("reset", 3)


def test_learning_preference_api_requires_exact_reset_confirmation(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "nova.db"
    application = create_app(
        Settings(
            intake_path=tmp_path / "intake",
            database_path=database_path,
            intake_scan_seconds=60,
            ocr_enabled=False,
        )
    )

    with TestClient(application, headers=LOCAL_ACTION_HEADERS) as client:
        with closing(sqlite3.connect(database_path)) as connection:
            _record(connection, 1, "Financial/Preferred")
            _record(connection, 2, "Financial/Preferred")
            _record(connection, 3, "Financial/Preferred")
            connection.commit()

        preferences = client.get("/api/v1/intake/preferences")
        rejected = client.post(
            "/api/v1/intake/preferences/reset",
            json={
                "document_type": "plain_text",
                "base_category": "Financial",
                "confirmation": "FORGET",
            },
        )
        reset = client.post(
            "/api/v1/intake/preferences/reset",
            json={
                "document_type": "plain_text",
                "base_category": "Financial",
                "confirmation": "FORGET plain_text / Financial",
            },
        )

    assert preferences.status_code == 200
    assert preferences.json()[0]["eligible"] is True
    assert preferences.json()[0]["candidate_destination"] == "Financial/Preferred"
    assert rejected.status_code == 422
    assert reset.status_code == 200
    assert reset.json()["removed_examples"] == 3
