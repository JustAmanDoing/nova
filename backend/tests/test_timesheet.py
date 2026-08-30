import sqlite3
from _thread import RLock
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.services.database import migrate_database
from app.services.timesheet import (
    BRISBANE_TIMEZONE,
    OFFICIAL_TOLL_PRICE_URL,
    OfficialTollPriceResolver,
    TimesheetIntent,
    TimesheetService,
    TollPriceResolutionError,
)


def _service(tmp_path: Path) -> TimesheetService:
    database_path = tmp_path / "nova.db"
    with closing(sqlite3.connect(database_path)) as connection:
        migrate_database(connection)
    return TimesheetService(
        str(database_path),
        RLock(),
        now=lambda: datetime(2026, 8, 21, 17, 0, tzinfo=BRISBANE_TIMEZONE),
    )


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


def test_progressive_capture_correction_derivation_and_persistence(tmp_path: Path) -> None:
    service = _service(tmp_path)

    first = service.match("loading started 5:15")
    assert first == TimesheetIntent("capture", (("loading_start", "05:15"),))
    assert service.execute(first).content == "Saved: loading start 5:15."
    service.execute(service.match("loading finished 6:10"))  # type: ignore[arg-type]
    service.execute(service.match("driving started 6:20"))  # type: ignore[arg-type]
    finish = service.execute(service.match("driving finished 4:45 pm"))  # type: ignore[arg-type]
    assert finish.content == "Saved: driving finish 16:45. Total hours: 11.50."

    correction = service.match("No, loading started 5:25")
    assert correction is not None and correction.correction
    result = service.execute(correction)
    assert result.content == "Corrected: loading start 5:25. Total hours: 11.33."

    reopened = TimesheetService(
        service.database_path,
        RLock(),
        now=lambda: datetime(2026, 8, 21, 18, 0, tzinfo=BRISBANE_TIMEZONE),
    )
    shift = reopened.get_shift("2026-08-21")
    assert shift is not None
    assert shift.loading_start == "05:25"
    assert shift.total_minutes == 680

    with closing(sqlite3.connect(service.database_path)) as connection:
        total_events = connection.execute(
            "SELECT event_type, previous_value, new_value FROM timesheet_events "
            "WHERE field_name = 'total_minutes' ORDER BY sequence"
        ).fetchall()
    assert total_events == [("field_saved", None, "690"), ("field_corrected", "690", "680")]


def test_invalid_time_is_not_automatically_saved(tmp_path: Path) -> None:
    service = _service(tmp_path)

    assert service.match("loading started 29:90") == TimesheetIntent("unsupported")
    assert service.get_shift() is None


def test_owner_word_order_combined_times_and_repeated_toll_quantity_are_parsed(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)

    assert service.match("Start time 5am") == TimesheetIntent(
        "capture", (("loading_start", "05:00"),)
    )
    assert service.match("Finish loading 6am") == TimesheetIntent(
        "capture", (("loading_finish", "06:00"),)
    )
    assert service.match("Start driving 6am finished driving 6pm") == TimesheetIntent(
        "capture",
        (("driving_start", "06:00"), ("driving_finish", "18:00")),
    )
    assert service.match("2 gateway tolls") == TimesheetIntent(
        "capture", toll_points=("Murarrie", "Murarrie")
    )

    service.execute(service.match("Start time 5am"))  # type: ignore[arg-type]
    result = service.execute(
        service.match("Start driving 6am finished driving 6pm")  # type: ignore[arg-type]
    )
    assert result.content.endswith("Total hours: 13.00.")


@pytest.mark.parametrize(
    "content",
    (
        "Finish at 1pm",
        "Finished at 1pm",
        "Finished 1pm",
        "I finished at 1pm",
        "Finish time 1pm",
        "Finish time was 1pm",
        "Finish time is 1pm",
    ),
)
def test_driving_finish_shorthand_requires_unambiguous_current_shift_state(
    tmp_path: Path,
    content: str,
) -> None:
    service = _service(tmp_path)
    service.execute(service.match("driving started 6:30"))  # type: ignore[arg-type]

    intent = service.match(content)

    assert intent == TimesheetIntent("capture", (("driving_finish", "13:00"),))
    result = service.execute(intent)
    assert result.content == "Saved: driving finish 13:00."
    assert result.source.capability_id == "timesheet.capture"
    shift = service.get_shift("2026-08-21")
    assert shift is not None
    assert shift.driving_finish == "13:00"
    with closing(sqlite3.connect(service.database_path)) as connection:
        events = connection.execute(
            "SELECT event_type, field_name, new_value FROM timesheet_events "
            "WHERE field_name = 'driving_finish' ORDER BY sequence"
        ).fetchall()
    assert events == [("field_saved", "driving_finish", "13:00")]


@pytest.mark.parametrize(
    "content",
    (
        "What finishes at 1pm?",
        "Does the meeting finish at 1pm?",
        "If I finish at 1pm, will traffic be bad?",
        "We were talking about finishing at 1pm",
        "The movie finishes at 1pm",
        "Finish at 1pm?",
    ),
)
def test_driving_finish_shorthand_rejects_questions_hypotheticals_and_discussion(
    tmp_path: Path,
    content: str,
) -> None:
    service = _service(tmp_path)
    service.execute(service.match("driving started 6:30"))  # type: ignore[arg-type]

    assert service.match(content) is None

    shift = service.get_shift("2026-08-21")
    assert shift is not None
    assert shift.driving_finish is None
    with closing(sqlite3.connect(service.database_path)) as connection:
        event_count = connection.execute(
            "SELECT COUNT(*) FROM timesheet_events WHERE field_name = 'driving_finish'"
        ).fetchone()[0]
    assert event_count == 0


def test_driving_finish_shorthand_rejects_nonqualifying_structured_state(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    assert service.match("Finish at 1pm") is None

    service.execute(service.match("loading started 5am"))  # type: ignore[arg-type]
    assert service.match("Finish at 1pm") is None

    service.execute(service.match("driving started 6:30"))  # type: ignore[arg-type]
    assert service.match("Finish at 1pm", pending_field="odometer_finish") is None

    explicit_finish = service.match("driving finished 12:30pm")
    assert explicit_finish is not None
    service.execute(explicit_finish)
    assert service.match("Finish at 1pm") is None
    shift = service.get_shift("2026-08-21")
    assert shift is not None
    assert shift.driving_finish == "12:30"

    previous_day_root = tmp_path / "previous-day"
    previous_day_root.mkdir()
    previous_day = _service(previous_day_root)
    previous_day.execute(
        previous_day.match("driving started 6:30")  # type: ignore[arg-type]
    )
    next_day = TimesheetService(
        previous_day.database_path,
        RLock(),
        now=lambda: datetime(2026, 8, 22, 5, 0, tzinfo=BRISBANE_TIMEZONE),
    )
    assert next_day.match("Finish at 1pm") is None
    previous_shift = next_day.get_shift("2026-08-21")
    assert previous_shift is not None
    assert previous_shift.driving_start == "06:30"
    assert previous_shift.driving_finish is None


@pytest.mark.parametrize(
    "content",
    (
        "Start odometer 444775",
        "Start odometer is 444775",
        "Start odometer was 444775",
    ),
)
def test_start_odometer_shorthand_saves_the_start_reading(
    tmp_path: Path,
    content: str,
) -> None:
    service = _service(tmp_path)

    intent = service.match(content)

    assert intent == TimesheetIntent("capture", (("odometer_start", "444775"),))
    result = service.execute(intent)
    assert result.content == "Saved: odometer start 444,775."
    assert result.source.capability_id == "timesheet.capture"
    shift = service.get_shift("2026-08-21")
    assert shift is not None
    assert shift.odometer_start == 444775
    with closing(sqlite3.connect(service.database_path)) as connection:
        events = connection.execute(
            "SELECT event_type, field_name, new_value FROM timesheet_events "
            "WHERE field_name = 'odometer_start' ORDER BY sequence"
        ).fetchall()
    assert events == [("field_saved", "odometer_start", "444775")]


@pytest.mark.parametrize(
    "content",
    (
        "What does start odometer 444775 mean?",
        "If I start odometer 444775, will the totals change?",
        "We were discussing start odometer 444775",
        "For example, start odometer 444775",
    ),
)
def test_start_odometer_shorthand_rejects_ordinary_chat_boundaries(
    tmp_path: Path,
    content: str,
) -> None:
    service = _service(tmp_path)
    service.execute(service.match("loading started 5am"))  # type: ignore[arg-type]

    assert service.match(content) is None

    shift = service.get_shift("2026-08-21")
    assert shift is not None
    assert shift.odometer_start is None
    with closing(sqlite3.connect(service.database_path)) as connection:
        event_count = connection.execute(
            "SELECT COUNT(*) FROM timesheet_events WHERE field_name = 'odometer_start'"
        ).fetchone()[0]
    assert event_count == 0


@pytest.mark.parametrize(
    "content",
    (
        "Starting odometer 444,775 km",
        "Start odometer reading is 444,775 km",
        "Beginning odometer 444775",
        "Start mileage 444775",
    ),
)
def test_start_odometer_shorthand_does_not_expand_beyond_the_approved_family(
    tmp_path: Path,
    content: str,
) -> None:
    service = _service(tmp_path)

    intent = service.match(content)

    assert intent is None or intent.kind == "unsupported"
    assert service.get_shift("2026-08-21") is None
    with closing(sqlite3.connect(service.database_path)) as connection:
        event_count = connection.execute(
            "SELECT COUNT(*) FROM timesheet_events WHERE field_name = 'odometer_start'"
        ).fetchone()[0]
    assert event_count == 0


@pytest.mark.parametrize(
    "content",
    (
        "Could we discuss what start time would avoid traffic tomorrow?",
        "Let's talk about start time 5am for tomorrow.",
        "We were discussing how loading started at 5am in the example.",
        "If driving started at 6am, when would the motorway be quieter?",
        "How much is the Gateway toll compared with Kuraby and Loganlea?",
        "Is the Heathwood toll road near Murarrie?",
        "Gateway tolls are expensive compared with the Loganlea toll.",
        "Why do toll roads charge different prices?",
        "The traffic report mentioned Gateway and Murarrie.",
    ),
)
def test_ordinary_timesheet_language_is_not_matched_without_an_open_shift(
    tmp_path: Path,
    content: str,
) -> None:
    service = _service(tmp_path)

    assert service.match(content) is None
    assert service.get_shift() is None


def test_ordinary_timesheet_questions_stay_unmatched_during_an_open_shift(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    service.execute(service.match("loading started 5:15"))  # type: ignore[arg-type]

    assert service.match("Could we discuss whether loading usually starts at 5am?") is None
    assert service.match("How much is the Gateway toll compared with Heathwood?") is None

    shift = service.get_shift()
    assert shift is not None
    assert shift.loading_start == "05:15"
    assert shift.toll_points == ()


def test_completeness_asks_only_for_missing_required_inputs(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.execute(service.match("loading started 5:15"))  # type: ignore[arg-type]
    result = service.execute(TimesheetIntent("complete"))

    assert result.content == (
        "Still needed: loading finish, driving start, driving finish, odometer start, "
        "odometer finish, total deliveries."
    )
    assert "toll" not in result.content
    assert "total hours" not in result.content


def test_tolls_are_saved_by_name_and_normal_conversation_can_correct_them(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    save = service.execute(service.match("I went through the Kuraby toll"))  # type: ignore[arg-type]
    assert save.content == "Saved: toll Kuraby/Compton Road."
    correction = service.execute(service.match("No, that toll was Gateway"))  # type: ignore[arg-type]
    assert correction.content == "Corrected: toll Murarrie."

    shift = service.get_shift()
    assert shift is not None
    assert shift.toll_points == ("Murarrie",)


def test_bare_toll_names_are_separate_entries_only_during_an_open_shift(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    assert service.match("Gateway") is None

    service.execute(service.match("loading started 5:15"))  # type: ignore[arg-type]
    gateway = service.execute(service.match("Gateway"))  # type: ignore[arg-type]
    kuraby = service.execute(service.match("Kuraby"))  # type: ignore[arg-type]

    assert gateway.content == "Saved: toll Murarrie."
    assert kuraby.content == "Saved: toll Kuraby/Compton Road."
    shift = service.get_shift()
    assert shift is not None
    assert shift.toll_points == ("Murarrie", "Kuraby/Compton Road")


def test_toll_entry_order_is_stable_when_one_message_records_multiple_tolls(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    service.execute(service.match("Heathwood toll and Gateway toll"))  # type: ignore[arg-type]
    service.execute(service.match("No, the last toll was Loganlea"))  # type: ignore[arg-type]

    shift = service.get_shift()
    assert shift is not None
    assert shift.toll_points == ("Heathwood", "Loganlea")


def test_official_resolver_reads_current_class_four_prices_without_hard_coding() -> None:
    requested: list[str] = []
    resolver = OfficialTollPriceResolver(
        lambda url: requested.append(url) or _official_table()
    )

    prices = resolver.resolve()

    assert requested == [OFFICIAL_TOLL_PRICE_URL]
    assert prices.prices == {
        "Murarrie": 2074,
        "Kuraby/Compton Road": 1224,
        "Loganlea": 784,
        "Heathwood": 1295,
    }


def test_official_resolver_refuses_an_incomplete_or_changed_table() -> None:
    resolver = OfficialTollPriceResolver(lambda _url: "<html>changed</html>")

    with pytest.raises(TollPriceResolutionError):
        resolver.resolve()


def test_weekly_retrieval_uses_persisted_tolls_and_current_prices(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.price_resolver = OfficialTollPriceResolver(lambda _url: _official_table())
    service.execute(service.match("Heathwood toll and Gateway toll"))  # type: ignore[arg-type]
    service.execute(service.match("loading started 5:15"))  # type: ignore[arg-type]

    result = service.execute(TimesheetIntent("weekly"))

    assert "date 2026-08-21" in result.content
    assert "Weekly toll total: $33.69 for 2 recorded toll(s)" in result.content
    assert "current Linkt Class 4 heavy-commercial prices" in result.content
    assert OFFICIAL_TOLL_PRICE_URL in result.content


def test_completed_shift_is_retrievable_and_a_new_day_can_open(tmp_path: Path) -> None:
    service = _service(tmp_path)
    for message in (
        "loading started 5:15",
        "loading finished 6:00",
        "driving started 6:10",
        "driving finished 4:45 pm",
        "odometer start 123,400",
        "odometer finish 123,780",
        "14 deliveries",
    ):
        intent = service.match(message)
        assert intent is not None
        service.execute(intent)

    completed = service.execute(TimesheetIntent("complete"))
    assert completed.content.startswith("Timesheet complete.")
    assert service.get_shift("2026-08-21") is not None

    next_day = TimesheetService(
        service.database_path,
        RLock(),
        now=lambda: datetime(2026, 8, 22, 5, 0, tzinfo=BRISBANE_TIMEZONE),
    )
    next_day.execute(next_day.match("loading started 5:20"))  # type: ignore[arg-type]
    assert next_day.get_shift("2026-08-22") is not None


def test_explicit_new_day_rolls_a_full_previous_shift_and_preserves_each_day(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    for message in (
        "loading started 5:15",
        "loading finished 6:00",
        "driving started 6:10",
        "driving finished 4:45 pm",
        "odometer start 123,400",
        "odometer finish 123,780",
        "14 deliveries",
        "Loganlea toll",
        "Loganlea toll",
    ):
        intent = service.match(message)
        assert intent is not None
        service.execute(intent)

    next_day = TimesheetService(
        service.database_path,
        RLock(),
        now=lambda: datetime(2026, 8, 21, 14, 5, tzinfo=UTC),
        price_resolver=OfficialTollPriceResolver(lambda _url: _official_table()),
    )
    intent = next_day.match("Start a new day")
    assert intent == TimesheetIntent("new_day")
    assert next_day.execute(intent).content == (
        "Timesheet for 2026-08-21 completed. "
        "Started new timesheet for 2026-08-22."
    )

    next_day.execute(next_day.match("loading started 5:20"))  # type: ignore[arg-type]
    next_day.execute(next_day.match("Loganlea toll"))  # type: ignore[arg-type]
    next_day.execute(next_day.match("Loganlea toll"))  # type: ignore[arg-type]
    correction = next_day.execute(
        next_day.match("No, loading started 5:25")  # type: ignore[arg-type]
    )

    assert correction.content == "Corrected: loading start 5:25."
    previous = next_day.get_shift("2026-08-21")
    current = next_day.get_shift("2026-08-22")
    assert previous is not None
    assert previous.status == "complete"
    assert previous.loading_start == "05:15"
    assert previous.toll_points == ("Loganlea", "Loganlea")
    assert current is not None
    assert current.status == "open"
    assert current.loading_start == "05:25"
    assert current.toll_points == ("Loganlea", "Loganlea")

    current_summary = next_day.execute(TimesheetIntent("current")).content
    weekly_summary = next_day.execute(TimesheetIntent("weekly")).content
    assert "date 2026-08-22" in current_summary
    assert "tolls Loganlea, Loganlea" in current_summary
    assert "date 2026-08-21" in weekly_summary
    assert "date 2026-08-22" in weekly_summary
    assert "Weekly toll total: $31.36 for 4 recorded toll(s)" in weekly_summary

    restarted = TimesheetService(
        service.database_path,
        RLock(),
        now=lambda: datetime(2026, 8, 21, 14, 10, tzinfo=UTC),
    )
    assert restarted.get_shift("2026-08-21") == previous
    assert restarted.get_shift("2026-08-22") == current


def test_new_day_keeps_an_incomplete_previous_shift_open_and_asks_only_missing(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    service.execute(service.match("loading started 5:15"))  # type: ignore[arg-type]

    next_day = TimesheetService(
        service.database_path,
        RLock(),
        now=lambda: datetime(2026, 8, 21, 14, 1, tzinfo=UTC),
    )
    result = next_day.execute(next_day.match("Start a new day"))  # type: ignore[arg-type]

    assert result.content == (
        "Still needed for 2026-08-21 before starting 2026-08-22: "
        "loading finish, driving start, driving finish, odometer start, "
        "odometer finish, total deliveries."
    )
    previous = next_day.get_shift("2026-08-21")
    assert previous is not None
    assert previous.status == "open"
    assert previous.loading_start == "05:15"
    assert next_day.get_shift("2026-08-22") is None
    assert next_day.execute(TimesheetIntent("current")).content == (
        "No timesheet record has been started for 2026-08-22."
    )

    blocked_overwrite = next_day.execute(
        next_day.match("loading started 5:30")  # type: ignore[arg-type]
    )
    assert blocked_overwrite.content == result.content
    previous = next_day.get_shift("2026-08-21")
    assert previous is not None
    assert previous.loading_start == "05:15"

    previous_day_value = next_day.execute(
        next_day.match("loading finished 6:00")  # type: ignore[arg-type]
    )
    assert previous_day_value.content == (
        "Saved for 2026-08-21: loading finish 6:00."
    )
    previous = next_day.get_shift("2026-08-21")
    assert previous is not None
    assert previous.loading_finish == "06:00"


def test_new_day_is_idempotent_for_the_current_brisbane_date(tmp_path: Path) -> None:
    service = _service(tmp_path)

    first = service.execute(service.match("Start a new day"))  # type: ignore[arg-type]
    second = service.execute(service.match("Start a new day"))  # type: ignore[arg-type]

    assert first.content == "Started new timesheet for 2026-08-21."
    assert second.content == "Timesheet for 2026-08-21 is already open."
    with closing(sqlite3.connect(service.database_path)) as connection:
        shifts = connection.execute(
            "SELECT shift_date, status FROM timesheet_shifts ORDER BY shift_date"
        ).fetchall()
    assert shifts == [("2026-08-21", "open")]
