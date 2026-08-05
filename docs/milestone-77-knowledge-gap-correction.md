# Milestone 77 - Knowledge-Gap Suggestion Correction

**Finding date:** 3 August 2026

**Patch candidate:** 0.76.2

**Status:** Owner accepted on the private phone; ready to publish

## Owner finding

The owner reported that some **Suggested next additions** remained visible after
the corresponding information had been reviewed and approved. The expected
behavior is that a covered suggestion disappears immediately after approval.

## Verified cause

The Chat interface already refreshed pending proposals, approved records, and
the read-only knowledge-quality report after approval. The defect was in the
deterministic coverage vocabulary: five guided prompt starters used wording
that their matching requirements did not recognise.

The verified installed data demonstrated both examples reported through normal
use:

- an approved response preference beginning with `I prefer responses` did not
  cover **Response style**; and
- an approved record beginning with `my work context` did not cover **Work
  context or schedule**.

The same prompt-to-checklist drift could affect technology environment, home
responsibility, and dietary preference additions.

## Correction

The deterministic requirement vocabulary now recognises the exact concepts
used by NOVA's own guided prompts:

- `prefer responses`;
- `work context`;
- `technology environment`;
- `home responsibility`; and
- `dietary preference`.

The existing post-approval refresh remains unchanged. Once the backend reports
the requirement as covered, the React view removes it from **Suggested next
additions** without a page reload.

## Architecture and safety review

The correction passes architecture review because it changes only bounded,
deterministic matching vocabulary inside the existing modular monolith. It
does not add a model call, semantic search, a provider, automatic inference,
background writes, or a new source of truth.

The correction passes safety and privacy review because:

- only active, owner-approved, checksum-verified local records can cover a
  requirement;
- pending, rejected, retired, missing, changed, or invalid records still do
  not count;
- no knowledge is written, edited, promoted, uploaded, or deleted by the
  quality report; and
- owner approval remains required before permanent knowledge exists.

## Regression coverage

- Backend coverage proves each affected guided prompt closes its matching gap
  and returns the exact approved record identifier.
- Frontend coverage proves approval triggers a fresh quality request and the
  covered **Add through chat** control disappears.
- Existing knowledge integrity, freshness, retrieval, approval, lifecycle, and
  unavailable-report behavior remain under their existing tests.

## Verification evidence

- Backend lint and strict type checking passed.
- The complete backend suite passed: 159 tests with 93.11% coverage.
- Frontend lint, type checking, 52 tests, and the production build passed.
- Windows control validation, Compose validation, and all four GitHub checks
  passed.
- A verified pre-install backup was created as
  `nova-20260803T110128.624020Z.db` with SHA-256
  `02ddd94e3d728eab8a84453f5c66ae6208f33b515de307bd7c16a84a99df6bb7`.
- Local and private Tailscale health checks reported healthy `0.76.2`.
- The active database passed its read-only SQLite quick check after install.
- Docker continued to publish only on `127.0.0.1`, while Tailscale Serve
  remained tailnet-only.
- The installed quality report marked response style, work context, and
  technology environment as covered from the owner's existing approved local
  records.
- Browser validation confirmed those completed additions were absent while
  the five genuinely missing optional additions remained visible.

## Acceptance gate

Before publishing 0.76.2:

1. backend lint, strict type checking, and the complete test suite must pass;
2. frontend lint, type checking, complete tests, and production build must
   pass;
3. Windows controls, Compose validation, and production runtime checks must
   pass;
4. a verified backup must precede installation;
5. the installed private phone route must report healthy 0.76.2; and
6. the owner must confirm that the additions already approved now disappear
   from **Suggested next additions**.

## Owner acceptance

On 5 August 2026, the owner opened Tailscale on the phone, loaded NOVA through
the existing private route, refreshed Chat, and confirmed that the previously
approved suggestions were gone. This closes the final acceptance gate for the
0.76.2 correction.

The result confirms the intended bounded behavior: approved, verified local
knowledge closes its matching deterministic gap, while genuinely missing
optional additions remain available. No knowledge record was edited, merged,
retired, deleted, uploaded, or otherwise changed by the quality report.

## Exact next action

Merge the accepted correction, publish Release 0.76.2, refresh the local NOVA
Project Record from that exact release, and continue the separately approved
Milestone 78 Librarian implementation. No additional runtime authority is
approved by this correction.
