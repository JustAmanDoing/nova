import re
from dataclasses import dataclass

SEARCHABLE_COLUMNS = (
    "files.original_name",
    "files.relative_path",
    "understanding.title",
    "understanding.full_text",
    "understanding.evidence",
    "understanding.error",
    "recommendation.category",
    "recommendation.suggested_filename",
    "recommendation.destination",
    "recommendation.reasons",
    "approval.status",
    "approval.category",
    "approval.suggested_filename",
    "approval.destination",
)
MAX_SEARCH_TERMS = 12


@dataclass(frozen=True)
class SearchPlan:
    clause: str | None
    parameters: tuple[str, ...]
    rank_expression: str | None
    rank_parameters: tuple[str, ...]


def build_search_plan(query: str | None) -> SearchPlan:
    if query is None or not (normalized := query.strip()):
        return SearchPlan(None, (), None, ())

    clauses: list[str] = []
    parameters: list[str] = []
    rank_expressions: list[str] = []
    rank_parameters: list[str] = []
    for term in _search_terms(normalized):
        pattern = f"%{_escape_like(term)}%"
        clauses.append(
            "("
            + " OR ".join(
                f"{column} LIKE ? ESCAPE '\\'" for column in SEARCHABLE_COLUMNS
            )
            + ")"
        )
        parameters.extend([pattern] * len(SEARCHABLE_COLUMNS))
        rank_expressions.append(
            """
            CASE
                WHEN lower(files.original_name) = lower(?) THEN 120
                WHEN files.original_name LIKE ? ESCAPE '\\' THEN 100
                WHEN understanding.title LIKE ? ESCAPE '\\' THEN 90
                WHEN recommendation.suggested_filename LIKE ? ESCAPE '\\'
                  OR approval.suggested_filename LIKE ? ESCAPE '\\'
                    THEN 80
                WHEN files.relative_path LIKE ? ESCAPE '\\' THEN 70
                WHEN recommendation.category LIKE ? ESCAPE '\\'
                  OR recommendation.destination LIKE ? ESCAPE '\\'
                  OR approval.category LIKE ? ESCAPE '\\'
                  OR approval.destination LIKE ? ESCAPE '\\'
                    THEN 60
                WHEN understanding.full_text LIKE ? ESCAPE '\\' THEN 40
                WHEN understanding.evidence LIKE ? ESCAPE '\\'
                  OR recommendation.reasons LIKE ? ESCAPE '\\'
                  OR understanding.error LIKE ? ESCAPE '\\'
                    THEN 20
                ELSE 0
            END
            """
        )
        rank_parameters.extend(
            [
                term,
                pattern,
                pattern,
                pattern,
                pattern,
                pattern,
                pattern,
                pattern,
                pattern,
                pattern,
                pattern,
                pattern,
                pattern,
                pattern,
            ]
        )

    return SearchPlan(
        clause=" AND ".join(clauses) if clauses else None,
        parameters=tuple(parameters),
        rank_expression=" + ".join(rank_expressions) if rank_expressions else None,
        rank_parameters=tuple(rank_parameters),
    )


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _search_terms(query: str) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()
    for match in re.finditer(r'"([^"]+)"|(\S+)', query):
        value = (match.group(1) or match.group(2)).strip('"').strip()
        key = value.casefold()
        if not value or key in seen:
            continue
        terms.append(value)
        seen.add(key)
        if len(terms) == MAX_SEARCH_TERMS:
            break
    return terms
