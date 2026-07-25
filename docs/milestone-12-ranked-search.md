# Milestone 12 — Ranked local search

## Outcome

Nova 0.12.0 makes existing local search results more useful without adding a
cloud service, vector database, or second search index. All matching and
ranking remain deterministic SQL over the local SQLite inventory.

## Query behavior

- Multiple unquoted terms must each match somewhere in the same record.
- Text inside double quotes is treated as one phrase.
- Repeated terms are ignored.
- Processing is bounded to twelve distinct terms from the API's
  200-character query limit.
- SQL wildcard characters are escaped and treated as literal search text.

Search continues to cover filenames, relative paths, extracted titles and
text, evidence, safe extraction diagnostics, recommendations, and review
fields. Existing intake, understanding, extension, document-type, and review
filters still combine with the query.

## Ranking

Each matching term contributes its strongest field weight:

1. Exact filename.
2. Filename.
3. Extracted title.
4. Suggested filename.
5. Relative path.
6. Category or destination.
7. Extracted full text.
8. Evidence, explanation, or safe error detail.

Scores are summed for multi-term searches. Equal scores retain the existing
newest-first and path ordering.

## Architecture boundary

Query parsing and SQL-plan construction live in a dedicated search module,
separate from file scanning and guarded actions. The API still returns only
normalized records and previews, never full extracted content.

SQLite FTS5, embeddings, and semantic retrieval remain deferred until measured
data volume or user needs justify them. This milestone does not add AI and does
not change any approval, execution, learning, or file-safety behavior.
