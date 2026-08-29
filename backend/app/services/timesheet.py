import hashlib
import re
import sqlite3
from _thread import RLock
from collections.abc import Callable
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta, timezone
from html.parser import HTMLParser
from typing import Literal, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from app.services.chat import CapabilitySourceRecord

OFFICIAL_TOLL_PRICE_URL = (
    "https://www.linkt.com.au/using-toll-roads/about-brisbane-toll-roads/"
    "toll-pricing/brisbane"
)
BRISBANE_TIMEZONE = timezone(timedelta(hours=10), name="Australia/Brisbane")

_TIME_FIELDS = ("loading_start", "loading_finish", "driving_start", "driving_finish")
_REQUIRED_FIELDS = (
    "loading_start",
    "loading_finish",
    "driving_start",
    "driving_finish",
    "odometer_start",
    "odometer_finish",
    "total_deliveries",
)
_LABELS = {
    "shift_date": "date",
    "loading_start": "loading start",
    "loading_finish": "loading finish",
    "driving_start": "driving start",
    "driving_finish": "driving finish",
    "odometer_start": "odometer start",
    "odometer_finish": "odometer finish",
    "total_deliveries": "total deliveries",
    "total_minutes": "total hours",
}
_TOLL_ALIASES = {
    "heathwood": "Heathwood",
    "loganlea": "Loganlea",
    "kuraby": "Kuraby/Compton Road",
    "compton": "Kuraby/Compton Road",
    "gateway": "Murarrie",
    "murarrie": "Murarrie",
}
_CAPTURE_PATTERNS = {
    "loading_start": re.compile(
        r"\b(?:loading\s+(?:has\s+)?(?:start(?:ed)?|began)|start\s+time)"
        r"(?:\s+at)?\s+"
        r"(?P<value>\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b",
        re.IGNORECASE,
    ),
    "loading_finish": re.compile(
        r"\b(?:loading\s+(?:has\s+)?(?:finish(?:ed)?|ended|done)|"
        r"(?:finish(?:ed)?|end(?:ed)?)\s+loading)(?:\s+at)?\s+"
        r"(?P<value>\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b",
        re.IGNORECASE,
    ),
    "driving_start": re.compile(
        r"\b(?:driv(?:ing|e)\s+(?:has\s+)?(?:start(?:ed)?|began)|"
        r"(?:start(?:ed)?|begin|began)\s+driv(?:ing|e))(?:\s+at)?\s+"
        r"(?P<value>\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b",
        re.IGNORECASE,
    ),
    "driving_finish": re.compile(
        r"\b(?:driv(?:ing|e)\s+(?:has\s+)?(?:finish(?:ed)?|ended|done)|"
        r"(?:finish(?:ed)?|end(?:ed)?)\s+driv(?:ing|e))(?:\s+at)?\s+"
        r"(?P<value>\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b",
        re.IGNORECASE,
    ),
    "odometer_start": re.compile(
        r"\b(?:odometer|odo)\s+(?:start(?:ed)?|opening)(?:\s+(?:at|was|is))?\s+"
        r"(?P<value>\d[\d,]*)\b",
        re.IGNORECASE,
    ),
    "odometer_finish": re.compile(
        r"\b(?:odometer|odo)\s+(?:finish(?:ed)?|end(?:ed)?|closing)"
        r"(?:\s+(?:at|was|is))?\s+(?P<value>\d[\d,]*)\b",
        re.IGNORECASE,
    ),
    "total_deliveries": re.compile(
        r"\b(?:(?:total\s+)?deliveries(?:\s+(?:was|is|today))?\s*[:=]?\s*"
        r"(?P<after>\d+)|(?P<before>\d+)\s+deliveries)\b",
        re.IGNORECASE,
    ),
}


class TollPriceResolutionError(RuntimeError):
    """Raised when current official Brisbane toll prices cannot be verified."""


@dataclass(frozen=True)
class TimesheetIntent:
    kind: Literal[
        "capture", "current", "complete", "weekly", "new_day", "prompt", "unsupported"
    ]
    values: tuple[tuple[str, str], ...] = ()
    toll_points: tuple[str, ...] = ()
    correction: bool = False
    follow_up: Literal["odometer_finish"] | None = None


@dataclass(frozen=True)
class TimesheetShift:
    id: str
    shift_date: str
    status: str
    loading_start: str | None
    loading_finish: str | None
    driving_start: str | None
    driving_finish: str | None
    odometer_start: int | None
    odometer_finish: int | None
    total_deliveries: int | None
    total_minutes: int | None
    toll_points: tuple[str, ...]


@dataclass(frozen=True)
class TollPrices:
    prices: dict[str, int]
    fetched_at: str
    source_url: str = OFFICIAL_TOLL_PRICE_URL


@dataclass(frozen=True)
class TimesheetResult:
    content: str
    source: CapabilitySourceRecord


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag == "tr":
            self._row = []
        elif tag in {"th", "td"} and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"th", "td"} and self._cell is not None and self._row is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None


class OfficialTollPriceResolver:
    def __init__(self, fetch_html: Callable[[str], str] | None = None) -> None:
        self.fetch_html = fetch_html or self._fetch_html

    def resolve(self) -> TollPrices:
        try:
            html = self.fetch_html(OFFICIAL_TOLL_PRICE_URL)
            parser = _TableParser()
            parser.feed(html)
            prices = self._class_four_prices(parser.rows)
        except (HTTPError, URLError, OSError, ValueError) as error:
            raise TollPriceResolutionError(
                "Current official Brisbane toll prices could not be verified."
            ) from error
        return TollPrices(prices=prices, fetched_at=_timestamp())

    @staticmethod
    def _fetch_html(url: str) -> str:
        request = Request(url, headers={"User-Agent": "NOVA/0.82 toll-price-check"})
        with urlopen(request, timeout=10) as response:  # noqa: S310 - fixed HTTPS URL
            if response.geturl() != OFFICIAL_TOLL_PRICE_URL:
                raise ValueError("Unexpected redirect from the official toll source.")
            content = cast(bytes, response.read(2_000_000))
            return content.decode("utf-8")

    @staticmethod
    def _class_four_prices(rows: list[list[str]]) -> dict[str, int]:
        aliases = {
            "murarrie": "Murarrie",
            "kuraby/compton road": "Kuraby/Compton Road",
            "loganlea": "Loganlea",
            "heathwood": "Heathwood",
        }
        prices: dict[str, int] = {}
        for row in rows:
            if not row:
                continue
            point = aliases.get(row[0].strip().casefold())
            if point is None:
                continue
            currency = [cell for cell in row[1:] if re.fullmatch(r"\$\d+\.\d{2}", cell)]
            if len(currency) < 4:
                continue
            dollars, cents = currency[3][1:].split(".")
            prices[point] = int(dollars) * 100 + int(cents)
        if set(prices) != set(aliases.values()):
            raise ValueError("The official Class 4 toll table was incomplete.")
        return prices


class TimesheetService:
    def __init__(
        self,
        database_path: str,
        operation_lock: RLock,
        *,
        now: Callable[[], datetime] | None = None,
        price_resolver: OfficialTollPriceResolver | None = None,
    ) -> None:
        self.database_path = database_path
        self.operation_lock = operation_lock
        self.now = now or (lambda: datetime.now(BRISBANE_TIMEZONE))
        self.price_resolver = price_resolver or OfficialTollPriceResolver()

    def match(
        self,
        content: str,
        *,
        pending_field: Literal["odometer_finish"] | None = None,
    ) -> TimesheetIntent | None:
        normalized = " ".join(content.split())
        lowered = normalized.casefold().rstrip(".!?")
        if re.fullmatch(
            r"(?:start|begin)(?: a)? new (?:work ?)?day(?: timesheet)?",
            lowered,
        ):
            return TimesheetIntent("new_day")
        if re.fullmatch(
            r"(?:show|read|get|retrieve)(?: me)? "
            r"(?:my |the )?(?:current|today'?s) timesheet",
            lowered,
        ):
            return TimesheetIntent("current")
        if re.fullmatch(
            r"(?:show|read|get|calculate)(?: me)? "
            r"(?:my |the )?(?:weekly|this week'?s) timesheet",
            lowered,
        ) or lowered == "weekly timesheet":
            return TimesheetIntent("weekly")
        if re.fullmatch(
            r"(?:(?:finish|complete|check) (?:my |the )?timesheet|"
            r"(?:end|finish) (?:my |the )?shift|is (?:my |the )?timesheet complete)",
            lowered,
        ) or re.fullmatch(
            r"(?:(?:i(?:'|’)?m|i am) )?(?:finished|done) for (?:the )?day",
            lowered,
        ):
            return TimesheetIntent("complete")
        if self._is_ordinary_timesheet_discussion(normalized, lowered):
            return None

        values: list[tuple[str, str]] = []
        for field, pattern in _CAPTURE_PATTERNS.items():
            match = pattern.search(normalized)
            if match is None:
                continue
            raw = match.groupdict().get("value")
            if raw is None:
                raw = match.groupdict().get("after") or match.groupdict().get("before")
            if raw is None:
                continue
            try:
                value = (
                    _parse_time(raw)
                    if field in _TIME_FIELDS
                    else str(int(raw.replace(",", "")))
                )
            except ValueError:
                continue
            values.append((field, value))

        if not values and pending_field == "odometer_finish":
            numeric_follow_up = re.fullmatch(r"\s*(\d[\d,]*)\s*", normalized)
            if numeric_follow_up is not None:
                values.append(
                    (
                        "odometer_finish",
                        str(int(numeric_follow_up.group(1).replace(",", ""))),
                    )
                )

        toll_points: list[str] = []
        toll_alias = "|".join(re.escape(alias) for alias in _TOLL_ALIASES)
        direct_toll_entry = bool(
            re.fullmatch(
                rf"(?:(?:\d+\s+)?(?:{toll_alias})(?:\s+tolls?)?)"
                rf"(?:\s*(?:,|and)\s*(?:\d+\s+)?(?:{toll_alias})"
                r"(?:\s+tolls?)?)*",
                lowered,
            )
            and re.search(r"\b(?:\d+|tolls?)\b", lowered)
        )
        has_toll_context = bool(
            direct_toll_entry
            or re.search(r"\b(?:through|used|crossed|passed)\b", lowered)
            or (
                re.search(r"\b(?:tolls?|surcharges?)\b", lowered)
                and re.search(
                    r"\b(?:save|record|log|correct|update|no|actually)\b",
                    lowered,
                )
            )
        )
        bare_toll_entry = bool(
            re.fullmatch(
                r"(?:heathwood|loganlea|kuraby|compton(?: road)?|gateway|murarrie)"
                r"(?:\s*(?:,|and)\s*"
                r"(?:heathwood|loganlea|kuraby|compton(?: road)?|gateway|murarrie))*",
                lowered,
            )
        ) and self._has_open_shift()
        if has_toll_context or bare_toll_entry:
            toll_matches: list[tuple[int, str, int]] = []
            for alias, point in _TOLL_ALIASES.items():
                pattern = re.compile(
                    rf"(?:(?P<count>\d+)\s+)?\b{re.escape(alias)}\b"
                )
                for match in pattern.finditer(lowered):
                    count = int(match.group("count") or "1")
                    if 1 <= count <= 50:
                        toll_matches.append((match.start(), point, count))
            for _position, point, count in sorted(toll_matches):
                toll_points.extend(point for _ in range(count))
        if not values and not toll_points:
            if re.fullmatch(
                r"(?:(?:finish|finished|end) (?:the )?(?:odometer|odo)|"
                r"(?:odometer|odo) (?:finish|finished|end))",
                lowered,
            ) and self._has_open_shift():
                return TimesheetIntent("prompt", follow_up="odometer_finish")
            if self._looks_like_timesheet_workflow(lowered):
                return TimesheetIntent("unsupported")
            return None
        correction = bool(re.match(r"\s*(?:no\b|actually\b|correction\b)", lowered))
        return TimesheetIntent(
            "capture", tuple(values), tuple(toll_points), correction=correction
        )

    def execute(self, intent: TimesheetIntent) -> TimesheetResult:
        if intent.kind == "capture":
            content = self._capture(intent)
            capability_id = "timesheet.capture"
        elif intent.kind == "current":
            content = self._current_summary()
            capability_id = "timesheet.current"
        elif intent.kind == "complete":
            content = self._complete()
            capability_id = "timesheet.complete"
        elif intent.kind == "weekly":
            content = self._weekly_summary()
            capability_id = "timesheet.weekly"
        elif intent.kind == "new_day":
            content = self._start_new_day()
            capability_id = "timesheet.new_day"
        elif intent.kind == "prompt":
            content = "What was the odometer finish reading?"
            capability_id = "timesheet.awaiting_odometer_finish"
        else:
            content = (
                "I couldn't safely save that timesheet detail. Please provide a "
                'supported field and value, for example: "loading finished 6am".'
            )
            capability_id = "timesheet.clarification"
        generated_at = _timestamp()
        is_weekly = intent.kind == "weekly"
        source_url = OFFICIAL_TOLL_PRICE_URL if is_weekly else "/chat.html"
        source = CapabilitySourceRecord(
            capability_id=capability_id,
            source_title=(
                "Official Linkt Brisbane toll prices"
                if is_weekly
                else "NOVA structured timesheet"
            ),
            source_url=source_url,
            generated_at=generated_at,
            result_sha256=hashlib.sha256(content.encode()).hexdigest(),
        )
        return TimesheetResult(content, source)

    def get_shift(self, shift_date: str | None = None) -> TimesheetShift | None:
        with closing(self._connection()) as connection:
            if shift_date is None:
                row = connection.execute(
                    "SELECT * FROM timesheet_shifts ORDER BY shift_date DESC LIMIT 1"
                ).fetchone()
            else:
                row = connection.execute(
                    "SELECT * FROM timesheet_shifts WHERE shift_date = ?", (shift_date,)
                ).fetchone()
            return self._record(connection, row) if row is not None else None

    def _has_open_shift(self) -> bool:
        with closing(self._connection()) as connection:
            return (
                connection.execute(
                    "SELECT 1 FROM timesheet_shifts WHERE status = 'open' LIMIT 1"
                ).fetchone()
                is not None
            )

    @staticmethod
    def _is_ordinary_timesheet_discussion(content: str, lowered: str) -> bool:
        if re.search(r"\b(?:save|record|log|correct|update)\b", lowered):
            return False
        if re.search(
            r"\b(?:discuss|discussing|discussion|talk|talking|example|hypothetical)\b",
            lowered,
        ):
            return True
        return bool(
            content.endswith("?")
            and re.match(
                r"(?:if|what|when|where|why|how|is|are|can|could|would|should|"
                r"do|does|did|will)\b",
                lowered,
            )
        )

    def _looks_like_timesheet_workflow(self, content: str) -> bool:
        if re.search(r"\b(?:timesheet|shift)\b", content):
            return True
        action = r"(?:start(?:ed)?|begin|began|finish(?:ed)?|end(?:ed)?|done)"
        field = r"(?:loading|driv(?:ing|e)|odometer|odo)"
        if re.search(rf"\b(?:{field}\b.*\b{action}|{action}\b.*\b{field})\b", content):
            return True
        if re.search(r"\bstart\s+time\b", content):
            return True
        if re.search(r"\b(?:delivery|deliveries)\b", content):
            return bool(
                self._has_open_shift()
                and re.search(r"\d|\b(?:total|save|record|correct|no|actually)\b", content)
            )
        if re.search(r"\b(?:tolls?|surcharges?)\b", content):
            return bool(
                self._has_open_shift()
                and re.search(
                    r"\d|\b(?:save|record|log|correct|update|no|actually)\b",
                    content,
                )
            )
        return bool(
            self._has_open_shift()
            and re.fullmatch(
                r"(?:heathwood|loganlea|kuraby|compton(?: road)?|gateway|murarrie)",
                content,
            )
        )

    def _capture(self, intent: TimesheetIntent) -> str:
        timestamp = _timestamp()
        current_date = self._brisbane_date().isoformat()
        confirmations: list[str] = []
        with self.operation_lock, closing(self._connection()) as connection, connection:
            row = self._open_or_today(connection, timestamp, current_date)
            shift_id = str(row["id"])
            shift_date = str(row["shift_date"])
            is_previous_day = shift_date != current_date
            fills_only_missing = bool(intent.values) and not intent.toll_points and all(
                row[field] is None for field, _value in intent.values
            )
            if is_previous_day and not intent.correction and not fills_only_missing:
                return self._missing_before_new_day(row, current_date)
            previous_total = row["total_minutes"]
            for field, value in intent.values:
                previous = row[field]
                converted: str | int = value if field in _TIME_FIELDS else int(value)
                event = "field_corrected" if previous is not None else "field_saved"
                connection.execute(
                    f"UPDATE timesheet_shifts SET {field} = ?, updated_at = ? WHERE id = ?",
                    (converted, timestamp, shift_id),
                )
                self._event(connection, shift_id, event, field, previous, converted, timestamp)
                confirmations.append(f"{_LABELS[field]} {_display(field, converted)}")
                row = connection.execute(
                    "SELECT * FROM timesheet_shifts WHERE id = ?", (shift_id,)
                ).fetchone()
            for point in intent.toll_points:
                if intent.correction:
                    existing = connection.execute(
                        "SELECT id, toll_point FROM timesheet_tolls WHERE shift_id = ? "
                        "ORDER BY sequence DESC LIMIT 1",
                        (shift_id,),
                    ).fetchone()
                else:
                    existing = None
                if existing is not None:
                    connection.execute(
                        "UPDATE timesheet_tolls SET toll_point = ?, updated_at = ? WHERE id = ?",
                        (point, timestamp, existing["id"]),
                    )
                    self._event(
                        connection,
                        shift_id,
                        "toll_corrected",
                        "toll",
                        existing["toll_point"],
                        point,
                        timestamp,
                    )
                else:
                    connection.execute(
                        "INSERT INTO timesheet_tolls "
                        "(id, shift_id, toll_point, created_at, updated_at) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (str(uuid4()), shift_id, point, timestamp, timestamp),
                    )
                    self._event(connection, shift_id, "toll_added", "toll", None, point, timestamp)
                confirmations.append(f"toll {point}")
            total_minutes = _derive_total_minutes(row)
            connection.execute(
                "UPDATE timesheet_shifts SET total_minutes = ?, updated_at = ? WHERE id = ?",
                (total_minutes, timestamp, shift_id),
            )
            if total_minutes is not None and total_minutes != previous_total:
                event = "field_corrected" if previous_total is not None else "field_saved"
                self._event(
                    connection,
                    shift_id,
                    event,
                    "total_minutes",
                    previous_total,
                    total_minutes,
                    timestamp,
                )
        prefix = "Corrected" if intent.correction else "Saved"
        if is_previous_day:
            prefix += f" for {shift_date}"
        content = f"{prefix}: " + "; ".join(confirmations) + "."
        if total_minutes is not None:
            content += f" Total hours: {_hours(total_minutes)}."
        return content

    def _current_summary(self) -> str:
        current_date = self._brisbane_date().isoformat()
        shift = self.get_shift(current_date)
        if shift is None:
            return f"No timesheet record has been started for {current_date}."
        return self._format_shift(shift)

    def _complete(self) -> str:
        timestamp = _timestamp()
        with self.operation_lock, closing(self._connection()) as connection, connection:
            row = connection.execute(
                "SELECT * FROM timesheet_shifts WHERE status = 'open'"
            ).fetchone()
            if row is None:
                return "There is no open timesheet record to complete."
            missing = self._missing_fields(row)
            if missing:
                return "Still needed: " + ", ".join(_LABELS[field] for field in missing) + "."
            self._complete_row(connection, row, timestamp)
            completed = connection.execute(
                "SELECT * FROM timesheet_shifts WHERE id = ?", (row["id"],)
            ).fetchone()
            record = self._record(connection, completed)
        return "Timesheet complete. " + self._format_shift(record)

    def _weekly_summary(self) -> str:
        today = self._brisbane_date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        with closing(self._connection()) as connection:
            rows = connection.execute(
                "SELECT * FROM timesheet_shifts WHERE shift_date BETWEEN ? AND ? "
                "ORDER BY shift_date",
                (week_start.isoformat(), week_end.isoformat()),
            ).fetchall()
            shifts = [self._record(connection, row) for row in rows]
        if not shifts:
            return "No timesheet records are saved for this week."
        tolls = [point for shift in shifts for point in shift.toll_points]
        lines = [self._format_shift(shift) for shift in shifts]
        if not tolls:
            lines.append("Weekly toll total: $0.00 (no toll entries recorded).")
            return "\n".join(lines)
        try:
            prices = self.price_resolver.resolve()
        except TollPriceResolutionError:
            lines.append(
                "Weekly toll total could not be calculated because the current official "
                f"Class 4 prices could not be verified. Source: {OFFICIAL_TOLL_PRICE_URL}"
            )
            return "\n".join(lines)
        cents = sum(prices.prices[point] for point in tolls)
        lines.append(
            f"Weekly toll total: ${cents / 100:.2f} for {len(tolls)} recorded toll(s), "
            f"using current Linkt Class 4 heavy-commercial prices. Source: {prices.source_url}"
        )
        return "\n".join(lines)

    def _start_new_day(self) -> str:
        timestamp = _timestamp()
        current_date = self._brisbane_date().isoformat()
        completed_previous: str | None = None
        with self.operation_lock, closing(self._connection()) as connection, connection:
            open_row = connection.execute(
                "SELECT * FROM timesheet_shifts WHERE status = 'open'"
            ).fetchone()
            if open_row is not None:
                open_date = str(open_row["shift_date"])
                if open_date == current_date:
                    return f"Timesheet for {current_date} is already open."
                if open_date > current_date:
                    return (
                        f"Cannot start {current_date} while the future-dated timesheet "
                        f"for {open_date} is open."
                    )
                missing = self._missing_fields(open_row)
                if missing:
                    return self._missing_before_new_day(open_row, current_date)
                self._complete_row(connection, open_row, timestamp)
                completed_previous = open_date

            current_row = connection.execute(
                "SELECT * FROM timesheet_shifts WHERE shift_date = ?", (current_date,)
            ).fetchone()
            if current_row is not None:
                return f"Timesheet for {current_date} is already {current_row['status']}."
            self._create_shift(connection, current_date, timestamp)

        started = f"Started new timesheet for {current_date}."
        if completed_previous is None:
            return started
        return f"Timesheet for {completed_previous} completed. {started}"

    def _open_or_today(
        self,
        connection: sqlite3.Connection,
        timestamp: str,
        shift_date: str,
    ) -> sqlite3.Row:
        row = connection.execute(
            "SELECT * FROM timesheet_shifts WHERE status = 'open'"
        ).fetchone()
        if row is not None:
            open_date = str(row["shift_date"])
            if open_date == shift_date:
                return cast(sqlite3.Row, row)
            if open_date > shift_date or self._missing_fields(row):
                return cast(sqlite3.Row, row)
            self._complete_row(connection, row, timestamp)
        row = connection.execute(
            "SELECT * FROM timesheet_shifts WHERE shift_date = ?", (shift_date,)
        ).fetchone()
        if row is not None:
            return cast(sqlite3.Row, row)
        return self._create_shift(connection, shift_date, timestamp)

    def _create_shift(
        self,
        connection: sqlite3.Connection,
        shift_date: str,
        timestamp: str,
    ) -> sqlite3.Row:
        shift_id = str(uuid4())
        connection.execute(
            "INSERT INTO timesheet_shifts "
            "(id, shift_date, status, created_at, updated_at) VALUES (?, ?, 'open', ?, ?)",
            (shift_id, shift_date, timestamp, timestamp),
        )
        self._event(connection, shift_id, "opened", "shift_date", None, shift_date, timestamp)
        return cast(
            sqlite3.Row,
            connection.execute(
                "SELECT * FROM timesheet_shifts WHERE id = ?", (shift_id,)
            ).fetchone(),
        )

    @staticmethod
    def _missing_fields(row: sqlite3.Row) -> list[str]:
        return [field for field in _REQUIRED_FIELDS if row[field] is None]

    def _missing_before_new_day(self, row: sqlite3.Row, current_date: str) -> str:
        missing = self._missing_fields(row)
        return (
            f"Still needed for {row['shift_date']} before starting {current_date}: "
            + ", ".join(_LABELS[field] for field in missing)
            + "."
        )

    def _brisbane_date(self) -> date:
        current = self.now()
        if current.tzinfo is None:
            current = current.replace(tzinfo=BRISBANE_TIMEZONE)
        return current.astimezone(BRISBANE_TIMEZONE).date()

    @classmethod
    def _complete_row(
        cls,
        connection: sqlite3.Connection,
        row: sqlite3.Row,
        timestamp: str,
    ) -> None:
        connection.execute(
            "UPDATE timesheet_shifts SET status = 'complete', completed_at = ?, "
            "updated_at = ? WHERE id = ?",
            (timestamp, timestamp, row["id"]),
        )
        cls._event(connection, str(row["id"]), "completed", None, None, None, timestamp)

    @staticmethod
    def _event(
        connection: sqlite3.Connection,
        shift_id: str,
        event_type: str,
        field: str | None,
        previous: object,
        new: object,
        timestamp: str,
    ) -> None:
        connection.execute(
            "INSERT INTO timesheet_events "
            "(shift_id, event_type, field_name, previous_value, new_value, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (shift_id, event_type, field, _optional_text(previous), _optional_text(new), timestamp),
        )

    @staticmethod
    def _record(connection: sqlite3.Connection, row: sqlite3.Row) -> TimesheetShift:
        toll_rows = connection.execute(
            "SELECT toll_point FROM timesheet_tolls WHERE shift_id = ? "
            "ORDER BY sequence",
            (row["id"],),
        ).fetchall()
        return TimesheetShift(
            id=str(row["id"]), shift_date=str(row["shift_date"]), status=str(row["status"]),
            loading_start=_optional_text(row["loading_start"]),
            loading_finish=_optional_text(row["loading_finish"]),
            driving_start=_optional_text(row["driving_start"]),
            driving_finish=_optional_text(row["driving_finish"]),
            odometer_start=_optional_int(row["odometer_start"]),
            odometer_finish=_optional_int(row["odometer_finish"]),
            total_deliveries=_optional_int(row["total_deliveries"]),
            total_minutes=_optional_int(row["total_minutes"]),
            toll_points=tuple(str(toll["toll_point"]) for toll in toll_rows),
        )

    @staticmethod
    def _format_shift(shift: TimesheetShift) -> str:
        values = [
            f"date {shift.shift_date}",
            f"loading {_range(shift.loading_start, shift.loading_finish)}",
            f"driving {_range(shift.driving_start, shift.driving_finish)}",
            f"odometer {_range(shift.odometer_start, shift.odometer_finish)}",
            "deliveries "
            f"{shift.total_deliveries if shift.total_deliveries is not None else 'missing'}",
            "total hours "
            f"{_hours(shift.total_minutes) if shift.total_minutes is not None else 'pending'}",
            "tolls " + (", ".join(shift.toll_points) if shift.toll_points else "none recorded"),
        ]
        return "Timesheet: " + "; ".join(values) + "."

    def _connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection


def _parse_time(value: str) -> str:
    compact = value.strip().lower().replace(" ", "")
    match = re.fullmatch(r"(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?(?P<period>am|pm)?", compact)
    if match is None:
        raise ValueError("Invalid time.")
    hour = int(match.group("hour"))
    minute = int(match.group("minute") or "0")
    period = match.group("period")
    if (
        minute > 59
        or (period is not None and not 1 <= hour <= 12)
        or (period is None and hour > 23)
    ):
        raise ValueError("Invalid time.")
    if period == "am":
        hour %= 12
    elif period == "pm":
        hour = (hour % 12) + 12
    return f"{hour:02d}:{minute:02d}"


def _derive_total_minutes(row: sqlite3.Row) -> int | None:
    if row["loading_start"] is None or row["driving_finish"] is None:
        return None
    start = time.fromisoformat(str(row["loading_start"]))
    finish = time.fromisoformat(str(row["driving_finish"]))
    start_minutes = start.hour * 60 + start.minute
    finish_minutes = finish.hour * 60 + finish.minute
    if finish_minutes < start_minutes:
        finish_minutes += 24 * 60
    return finish_minutes - start_minutes


def _display(field: str, value: str | int) -> str:
    return _display_time(str(value)) if field in _TIME_FIELDS else f"{int(value):,}"


def _display_time(value: str) -> str:
    hour, minute = (int(part) for part in value.split(":"))
    return f"{hour}:{minute:02d}"


def _hours(minutes: int) -> str:
    return f"{minutes / 60:.2f}"


def _range(start: object, finish: object) -> str:
    left = _display_time(str(start)) if isinstance(start, str) else start
    right = _display_time(str(finish)) if isinstance(finish, str) else finish
    return f"{left if left is not None else 'missing'}–{right if right is not None else 'missing'}"


def _optional_text(value: object) -> str | None:
    return str(value) if value is not None else None


def _optional_int(value: object) -> int | None:
    return int(cast(int | str, value)) if value is not None else None


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()
