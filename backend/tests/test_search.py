from app.services.search import (
    MAX_SEARCH_TERMS,
    SEARCHABLE_COLUMNS,
    build_search_plan,
)


def test_empty_search_has_no_clause_or_ranking() -> None:
    assert build_search_plan(None).clause is None
    assert build_search_plan("   ").rank_expression is None


def test_search_plan_deduplicates_terms_and_preserves_quoted_phrases() -> None:
    plan = build_search_plan('invoice INVOICE "Annual Report"')

    assert plan.clause is not None
    assert plan.rank_expression is not None
    assert len(plan.parameters) == len(SEARCHABLE_COLUMNS) * 2
    assert plan.parameters[0] == "%invoice%"
    assert plan.parameters[len(SEARCHABLE_COLUMNS)] == "%Annual Report%"


def test_search_plan_escapes_like_wildcards_and_bounds_term_count() -> None:
    terms = ["100%_complete", *(f"term{index}" for index in range(20))]
    plan = build_search_plan(" ".join(terms))

    assert plan.parameters[0] == r"%100\%\_complete%"
    assert len(plan.parameters) == len(SEARCHABLE_COLUMNS) * MAX_SEARCH_TERMS
    assert len(plan.rank_parameters) == 14 * MAX_SEARCH_TERMS
