# Intake MVP completion review — 25 July 2026

## Decision

The guarded Intake MVP is complete and suitable for user acceptance. No
material architectural blocker remains within its approved scope.

This decision applies to Nova's local document workflow, not to the full
long-term assistant vision. Chat, semantic retrieval, automatic filing, memory,
plugins, agents, and external AI providers remain separate future product
decisions.

## Architectural assessment

The modular monolith remains proportionate to the current single-user,
local-first workload:

- React provides one local dashboard without duplicating business rules.
- FastAPI owns typed API, policy, and workflow boundaries.
- SQLite holds derived inventory, understanding, recommendations, reviews,
  audit events, and conservative learning in one recoverable datastore.
- Host-mounted intake, library, and backup folders keep user documents and
  verified snapshots outside the application image.
- Docker Compose provides a reproducible deployment without introducing
  microservices, a message bus, or a second search datastore.

The implementation preserves the approved separation:

`Observe → Understand → Recommend → Approve → Execute → Audit → Learn`

Approval never executes an action. Learning never approves an action.
Understanding and recommendation remain read-only. Execution remains separately
confirmed, containment-checked, no-overwrite, fingerprint-verified, audited, and
reversible when the recorded safety conditions still hold.

## Acceptance matrix

| Requirement | Evidence |
| --- | --- |
| Observe and fingerprint local files | Unit/integration suite and production runtime inventory |
| Exact-duplicate detection | Scanner and inventory tests |
| TXT and Markdown understanding | Unit tests and representative production fixtures |
| DOCX understanding | Direct XML extraction test and representative production fixture |
| PDF understanding | Direct text-layer extraction and representative production fixture |
| Local image OCR | Bounded OCR tests and real production Tesseract fixture |
| Structured extraction errors | Failure-isolation tests and safe public diagnostic fields |
| Explainable deterministic recommendation | Rule tests and production fixture recommendations |
| Filename and content search | Ranked search tests and production acceptance queries |
| Evidence and metadata/status search | API tests and production acceptance queries |
| Explicit review boundary | Review-state and stale-version tests |
| Guarded move and undo | Failure-path tests and isolated production workflow |
| Append-only action audit | Operation event tests and isolated production workflow |
| Conservative destination learning | Threshold, reset, and invalidation tests plus production refresh exercise |
| Verified online backup | Backup tests, guarded updater, and production workflow |
| Guarded restore and safety snapshot | Restore rollback tests and production workflow |
| Local-only network exposure | Loopback Compose bindings and live port verification |
| Database integrity | Startup guard, backup/restore checks, and live `quick_check` |
| Reproducible delivery | Pinned dependencies, actions, and container base digests |
| Windows operation | Start, stop, status, guarded update, backup, version, and readiness controls |

## Live deployment evidence

The guarded Windows updater was exercised against the running local
installation. It created a verified pre-update SQLite snapshot before applying
the approved source, rebuilt the pinned containers, waited for both services,
and reported the expected version. Existing inventory totals were unchanged,
the database integrity check returned `ok`, operational status had no warnings,
and the dashboard and API remained bound only to `127.0.0.1`.

## Residual risks

These are monitored constraints, not MVP blockers:

1. SQL `LIKE` search should be measured as the local corpus grows; FTS5 is
   justified only when observed latency becomes noticeable.
2. Full extracted text and backups may contain sensitive information and must
   remain private local data.
3. The current 50 GB-class free-space constraint should be monitored before
   adding large local AI models or retaining a much larger document corpus.
4. Recovery remains deliberately conservative: ambiguous interrupted actions
   are diagnosed for manual review rather than repaired automatically.

## Next product boundary

The next phase should begin only after normal user acceptance of the Intake MVP.
It should choose one product objective at a time. Search-backed chat and semantic
retrieval are natural candidates, but neither is implicitly approved by this
review. Automatic filing remains disabled until representative usage provides
measured accuracy and the user explicitly approves automation rules.
