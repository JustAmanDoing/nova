import json
import sqlite3
from _thread import RLock
from collections.abc import Iterator, Sequence
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services.chat import LocalModelProviderError, ModelRecord
from app.services.database import migrate_database
from app.services.timesheet import (
    BRISBANE_TIMEZONE,
    OfficialTollPriceResolver,
    TimesheetIntent,
    TimesheetService,
)

INTENT = {"X-Nova-Intent": "local-user-action"}


class FailingProvider:
    def list_models(self) -> list[ModelRecord]:
        return [
            ModelRecord(
                name="qwen3:8b",
                size_bytes=5_225_388_164,
                parameter_size="8.2B",
                quantization_level="Q4_K_M",
            )
        ]

    def stream_chat(
        self,
        model: str,
        messages: Sequence[dict[str, str]],
    ) -> Iterator[str]:
        del model, messages
        raise LocalModelProviderError("The local model provider is unavailable.")
        yield


def _official_table() -> str:
    return """
    <table>
      <tr><th>Toll point</th><th>Class 1</th><th>Class 2</th><th>Class 3</th><th>Class 4</th></tr>
      <tr><td>Murarrie</td><td>$3.00</td><td>$6.00</td><td>$12.00</td><td>$20.74</td></tr>
      <tr><td>Kuraby/Compton Road</td><td>$2.00</td><td>$4.00</td><td>$8.00</td><td>$12.24</td></tr>
      <tr><td>Loganlea</td><td>$1.00</td><td>$2.00</td><td>$4.00</td><td>$7.84</td></tr>
      <tr><td>Heathwood</td><td>$2.00</td><td>$4.00</td><td>$8.00</td><td>$12.95</td></tr>
    </table>
    """


def _service(tmp_path: Path, now: datetime | None = None) -> TimesheetService:
    database_path = tmp_path / "nova.db"
    with closing(sqlite3.connect(database_path)) as connection:
        migrate_database(connection)
    service = TimesheetService(
        str(database_path),
        RLock(),
        now=lambda: now
        or datetime(2026, 8, 31, 7, 0, tzinfo=BRISBANE_TIMEZONE),
        price_resolver=OfficialTollPriceResolver(lambda _url: _official_table()),
    )
    return service


def _application(tmp_path: Path):
    return create_app(
        Settings(
            intake_path=tmp_path / "intake",
            database_path=tmp_path / "nova.db",
            backup_path=tmp_path / "backups",
            intake_scan_seconds=60,
        )
    )


FIELD_FAMILIES = (
    ("loading_start", "05:00", ("Start time 5am", "Start time is 5am", "Start time was 5am")),
    (
        "loading_finish",
        "06:00",
        ("Finish loading 6am", "Finish loading is 6am", "Finish loading was 6am"),
    ),
    (
        "driving_start",
        "06:00",
        ("Start driving 6am", "Start driving is 6am", "Start driving was 6am"),
    ),
    (
        "driving_finish",
        "13:00",
        ("Finish time 1pm", "Finish time is 1pm", "Finish time was 1pm"),
    ),
    (
        "odometer_start",
        "444775",
        (
            "Start odometer 444775",
            "Start odometer is 444775",
            "Start odometer was 444775",
        ),
    ),
    (
        "odometer_finish",
        "444855",
        (
            "Finish odometer 444855",
            "Finish odometer is 444855",
            "Finish odometer was 444855",
        ),
    ),
    (
        "total_deliveries",
        "10",
        (
            "Total deliveries 10",
            "Total deliveries is 10",
            "Total deliveries was 10",
        ),
    ),
)


@pytest.mark.parametrize("field, expected, family", FIELD_FAMILIES)
def test_every_approved_direct_field_family_matches(
    tmp_path: Path,
    field: str,
    expected: str,
    family: tuple[str, str, str],
) -> None:
    for index, content in enumerate(family):
        case_root = tmp_path / f"{field}-{index}"
        case_root.mkdir()
        service = _service(case_root)
        service.execute(TimesheetIntent("new_day"))
        if field == "driving_finish":
            service.execute(TimesheetIntent("capture", (("driving_start", "06:30"),)))

        intent = service.match(content)

        assert intent is not None, content
        assert intent.kind == "capture", content
        assert intent.values == ((field, expected),), content
        result = service.execute(intent)
        assert result.source.capability_id == "timesheet.capture"
        shift = service.get_shift("2026-08-31")
        assert shift is not None
        stored = getattr(shift, field)
        if field in {"odometer_start", "odometer_finish", "total_deliveries"}:
            assert stored == int(expected)
        else:
            assert stored == expected


@pytest.mark.parametrize("model", [None, "qwen3:8b"])
@pytest.mark.parametrize("field, expected, family", FIELD_FAMILIES)
@pytest.mark.parametrize("family_index", [0, 1, 2])
def test_every_approved_direct_field_form_is_structured_through_real_chat(
    tmp_path: Path,
    model: str | None,
    field: str,
    expected: str,
    family: tuple[str, str, str],
    family_index: int,
) -> None:
    case_root = tmp_path / f"{field}-{family_index}-{model or 'none'}"
    case_root.mkdir()
    application = _application(case_root)
    with TestClient(application) as client:
        application.state.chat.provider = FailingProvider()
        application.state.timesheets.now = lambda: datetime(
            2026, 8, 31, 7, 0, tzinfo=BRISBANE_TIMEZONE
        )
        application.state.timesheets.execute(TimesheetIntent("new_day"))
        if field == "driving_finish":
            application.state.timesheets.execute(
                TimesheetIntent("capture", (("driving_start", "06:30"),))
            )
        conversation_id = client.post(
            "/api/v1/chat/conversations",
            headers=INTENT,
            json={"title": "Whole-timesheet audit"},
        ).json()["id"]

        response = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            headers=INTENT,
            json={"model": model, "content": family[family_index]},
        )

        assert response.status_code == 200
        events = [json.loads(line) for line in response.text.splitlines()]
        assert [event["type"] for event in events] == [
            "user",
            "capability",
            "delta",
            "done",
        ]
        assert events[1]["source"]["capability_id"] == "timesheet.capture"
        assert events[-1]["message"]["capability_sources"] == [events[1]["source"]]
        shift = application.state.timesheets.get_shift("2026-08-31")
        assert shift is not None
        stored = getattr(shift, field)
        if field in {"odometer_start", "odometer_finish", "total_deliveries"}:
            assert stored == int(expected)
        else:
            assert stored == expected


@pytest.mark.parametrize(
    "content",
    (
        "Start time is 5am?",
        "Finish loading is 6am?",
        "Start driving is 6am?",
        "Finish time is 1pm?",
        "Start odometer is 444775?",
        "Finish odometer is 444855?",
        "Total deliveries is 10?",
    ),
)
def test_question_shaped_field_turns_never_mutate_timesheet(
    tmp_path: Path,
    content: str,
) -> None:
    service = _service(tmp_path)
    service.execute(TimesheetIntent("new_day"))
    service.execute(TimesheetIntent("capture", (("driving_start", "06:30"),)))
    before = service.get_shift("2026-08-31")

    assert service.match(content) is None

    after = service.get_shift("2026-08-31")
    assert after == before


@pytest.mark.parametrize(
    "entry, expected",
    (
        ("2 gateway tolls", ("Murarrie", "Murarrie")),
        ("2 murarrie tolls", ("Murarrie", "Murarrie")),
        ("2 kuraby tolls", ("Kuraby/Compton Road", "Kuraby/Compton Road")),
        ("2 compton tolls", ("Kuraby/Compton Road", "Kuraby/Compton Road")),
        ("2 loganlea tolls", ("Loganlea", "Loganlea")),
        ("2 heathwood tolls", ("Heathwood", "Heathwood")),
    ),
)
def test_all_supported_toll_names_and_quantities_persist(
    tmp_path: Path,
    entry: str,
    expected: tuple[str, str],
) -> None:
    service = _service(tmp_path)
    intent = service.match(entry)
    assert intent == TimesheetIntent("capture", toll_points=expected)
    service.execute(intent)
    shift = service.get_shift("2026-08-31")
    assert shift is not None
    assert shift.toll_points == expected


def test_finish_odometer_prompt_and_numeric_follow_up_remain_supported(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.execute(TimesheetIntent("new_day"))
    prompt = service.match("Finish odometer")
    assert prompt == TimesheetIntent("prompt", follow_up="odometer_finish")
    follow_up = service.match("444855", pending_field="odometer_finish")
    assert follow_up == TimesheetIntent("capture", (("odometer_finish", "444855"),))
    service.execute(follow_up)
    shift = service.get_shift("2026-08-31")
    assert shift is not None
    assert shift.odometer_finish == 444855


def test_one_hundred_fake_days_complete_without_field_by_field_owner_testing(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "nova.db"
    with closing(sqlite3.connect(database_path)) as connection:
        migrate_database(connection)
    clock = [datetime(2026, 1, 1, 7, 0, tzinfo=BRISBANE_TIMEZONE)]
    service = TimesheetService(
        str(database_path),
        RLock(),
        now=lambda: clock[0],
        price_resolver=OfficialTollPriceResolver(lambda _url: _official_table()),
    )
    tolls = ("gateway", "kuraby", "loganlea", "heathwood")

    for day in range(100):
        date_text = clock[0].date().isoformat()
        started = service.execute(service.match("Start a new day"))  # type: ignore[arg-type]
        assert started.source.capability_id == "timesheet.new_day"

        family_index = day % 3
        odometer_start = 400_000 + day * 100
        odometer_finish = odometer_start + 80
        deliveries = 5 + (day % 20)
        entries = (
            FIELD_FAMILIES[0][2][family_index],
            FIELD_FAMILIES[1][2][family_index],
            FIELD_FAMILIES[2][2][family_index],
            FIELD_FAMILIES[3][2][family_index],
            FIELD_FAMILIES[4][2][family_index].replace("444775", str(odometer_start)),
            FIELD_FAMILIES[5][2][family_index].replace("444855", str(odometer_finish)),
            FIELD_FAMILIES[6][2][family_index].replace("10", str(deliveries)),
            f"2 {tolls[day % len(tolls)]} tolls",
        )
        for entry in entries:
            intent = service.match(entry)
            assert intent is not None, (date_text, entry)
            assert intent.kind == "capture", (date_text, entry, intent)
            result = service.execute(intent)
            assert result.source.capability_id == "timesheet.capture"

        completed = service.execute(service.match("I'm finished for the day"))  # type: ignore[arg-type]
        assert completed.content.startswith("Timesheet complete.")
        shift = service.get_shift(date_text)
        assert shift is not None
        assert shift.status == "complete"
        assert shift.loading_start == "05:00"
        assert shift.loading_finish == "06:00"
        assert shift.driving_start == "06:00"
        assert shift.driving_finish == "13:00"
        assert shift.odometer_start == odometer_start
        assert shift.odometer_finish == odometer_finish
        assert shift.total_deliveries == deliveries
        assert shift.total_minutes == 480
        assert len(shift.toll_points) == 2

        current = service.execute(service.match("Show me today's timesheet"))  # type: ignore[arg-type]
        assert date_text in current.content
        weekly = service.execute(service.match("Show me this week's timesheet"))  # type: ignore[arg-type]
        assert "Weekly toll total:" in weekly.content

        clock[0] += timedelta(days=1)
