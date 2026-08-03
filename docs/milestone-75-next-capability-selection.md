# Milestone 75 - Evidence-Led Next Capability Selection

**Completion date:** 3 August 2026

**Base release:** 0.74.0

**Decision:** Complete; Milestone 76 Local NOVA Project Record selected and
explicitly requested by the owner

## Objective

Choose one bounded capability after accepted Release 0.74.0. The selection
must reduce NOVA's dependence on ChatGPT chat history while preserving
local-first privacy, source traceability, owner control, recoverability, AI
optionality, and the modular-monolith architecture.

## Evidence used

- Release `0.74.0`, tag `v0.74.0`, GitHub `main`, and the installed runtime all
  resolve to commit `d00e35c66ebab1a0e9449f7cf0a4c55013f6e951`.
- The owner explicitly requested that all information about NOVA be stored
  locally in NOVA rather than depend on ChatGPT chats.
- The repository contains 131 milestone, architecture, operations, and release
  documents through Milestone 74.
- The approved knowledge directory contains 12 local, checksum-bound Markdown
  records.
- The cumulative development archive under `N:\Nova\Archive` ends at
  Milestone 59, while repository evidence continues through Milestone 74.
- The ChatGPT project source mirror remains a stale Release 0.52.0 snapshot and
  must not be treated as current.
- NOVA stores its own chat conversations locally in SQLite, but it has no
  project-record catalogue and no guarded path for importing NOVA-only
  ChatGPT exports.
- ChatGPT account history cannot be assumed accessible to NOVA. A source export
  must be explicitly supplied by the owner before it can be preserved locally.

No personal record content or unrelated conversation content is copied into
this decision document.

## Impact-first selection

Candidates are scored from 1 to 5 using the established impact-first method.

| Rank | Candidate | Impact | Evidence | Fit | Safety | Reuse | Delivery | Weighted |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Local NOVA project record and guarded chat migration | 5 | 5 | 5 | 5 | 5 | 4 | 4.95 |
| 2 | Complete remaining core knowledge | 4 | 4 | 5 | 5 | 5 | 5 | 4.45 |
| 3 | Broader document workspace | 4 | 3 | 4 | 4 | 5 | 3 | 3.85 |
| 4 | Dates and reminders | 5 | 3 | 3 | 3 | 3 | 2 | 3.75 |
| 5 | Voice conversation | 4 | 3 | 2 | 2 | 2 | 2 | 3.00 |

## Selected product slice

**Milestone 76 - Local NOVA Project Record**

Create a local, source-aware project record that makes current status,
milestone evidence, approved decisions, release state, local archive coverage,
and explicitly imported NOVA chat sources inspectable from NOVA.

The first slice will:

1. establish one current canonical project-status record;
2. catalogue repository documentation, local development archives, approved
   knowledge records, and imported raw chat sources without duplicating them;
3. keep raw imports immutable and checksum-bound outside Git;
4. expose the catalogue read-only through NOVA on PC and phone;
5. provide a guarded host-side import control for an explicitly selected
   NOVA-only `.txt`, `.md`, `.json`, `.html`, or `.zip` source;
6. record source name, import time, byte size, SHA-256, and local relative path;
7. keep imported chat text out of permanent approved knowledge until the owner
   separately approves a knowledge proposal; and
8. preserve existing backup, local networking, and action boundaries.

## Why this is the most urgent next step

- Project continuity currently depends partly on ChatGPT conversation context.
- The local archive gap is measured: Milestones 60-74 are documented in the
  repository but absent from the cumulative development archive.
- A canonical local record prevents stale chat summaries from outranking
  current repository and runtime evidence.
- The change improves disaster recovery and future model portability without
  granting NOVA any new external access or autonomous authority.
- It reuses the existing local storage, checksum, read-only API, responsive UI,
  Windows control, and verification patterns.

## Decision boundary

Milestone 75 authorises selection, proposal, and review. The owner's explicit
request also approves the bounded Milestone 76 goal, subject to the architecture
and engineering conditions recorded alongside this decision.

The scope does not authorise access to the owner's ChatGPT account, automatic
account export, unrelated-chat collection, semantic search, automatic memory
promotion, cloud upload, Git tracking of raw archives, or deletion of any
source chat.

## Completion estimate

- Practical local NOVA prototype: 100 percent.
- Broader long-term NOVA vision: approximately 86 percent.
- Milestone 75 decision work: 100 percent.

## Exact next action

Implement Milestone 76 on a feature branch, migrate the currently verified
project state into the local archive catalogue, validate one synthetic guarded
import, and request physical-owner acceptance before release.
