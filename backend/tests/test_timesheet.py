import sqlite3
from _thread import RLock
from contextlib import closing
from datetime import datetime
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
    assert finish.content == "Saved: driving finish 16:45. Total hours: 11.5."

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

    assert service.match("loading started 29:90") is None
    assert service.get_shift() is None


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
