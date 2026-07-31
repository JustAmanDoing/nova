# Milestone 68 - Windows and Browser Acceptance

**Acceptance date:** 31 July 2026

**Release:** 0.68.0

**Implementation commit:** `8888969a956c0c1bb4171aa977ac52c5be0b9a4c`

**Implementation merge commit:** `d74d8ec0e31eaa1774239a6443f76c10f32d70df`

**Decision:** Pass

## Protected verification

PR #11 ran the complete required matrix against the exact implementation
head:

- Backend quality - pass
- Frontend quality - pass
- Windows controls - pass
- Production runtime - pass

Run: `30614964095`

Merged `main` repeated the same four checks successfully.

Run: `30615056356`

The protected `main` branch requires all four checks, applies the rule to
administrators, and disables force pushes and branch deletion.

## Local installation

- The N-drive checkout fast-forwarded to implementation merge commit
  `d74d8ec`.
- A verified pre-install database backup was created before rebuilding:
  `nova-20260731T080628.853991Z.db`.
- Its independently recalculated SHA-256 matched:
  `f107f9cf9fcfdf10b522686cbc61ad2e76ef2a4f69b07cf62a5918bb0533ad38`.
- Containers rebuilt successfully and remained published only on
  `127.0.0.1`.
- Installed backend and frontend versions both report `0.68.0`.

## Database and recovery checks

| Check | Result |
| --- | --- |
| Active database integrity | `ok` |
| Schema version | 16 |
| Latest migration | `owner-approved-next-actions` |
| `next_actions` table | Present |
| `next_action_events` table | Present |
| Existing knowledge records after migration | 7 |
| Existing knowledge records after restore | 7 |

A post-install backup was created and independently hash-verified:

- file: `nova-20260731T081033.435306Z.db`
- SHA-256:
  `5b4cea953e68a0a67292d8886f2518e08da2dae3f350a3c72e72001ad62c909e`

The guarded restore accepted only the exact confirmation phrase, created a
verified safety backup
`nova-20260731T081033.751927Z.db`, restored successfully, and left schema,
knowledge, action counts, service health, and database integrity unchanged.

## Runtime and privacy checks

| Check | Result |
| --- | --- |
| Health version | `0.68.0` |
| API health | Pass |
| Backend container | Healthy |
| Frontend container | Running |
| Backend bind | `127.0.0.1:8000` only |
| Frontend bind | `127.0.0.1:5173` only |
| Private API `Cache-Control` | `no-store` |
| Frontend CSP | Pass |
| `nosniff` | Pass |
| Frame denial | Pass |
| Unexpected API Host | Rejected with 400 |
| Unexpected frontend Host | Connection closed |
| Mutation without local intent | Rejected with 403 |
| Empty action title | Rejected with 422 |
| Browser warnings and errors | None |

The rejected mutation and invalid-title checks left the action store empty.

## Browser checks

The installed `/focus.html` page was inspected in the connected local browser
at its normal desktop size and at a 390 by 844 phone-sized viewport.

Passed:

- correct release label, title, navigation, verified project, and verified
  goal;
- a separate Next actions region with an explicit owner-entry form;
- labelled title input and optional active-project selector;
- clear statement that NOVA does not add, rank, schedule, or infer actions;
- truthful loading, empty, open, and completed states;
- responsive single-column form and cards;
- no horizontal overflow at either size;
- visible native links, input, select, and buttons in deterministic keyboard
  order; and
- no console warning or error.

No synthetic action was added during automated browser inspection.

## Owner workflow acceptance

The owner entered the genuine action:

> Complete the Milestone 68 owner acceptance test.

The owner linked it to the verified active NOVA project and exercised:

1. create;
2. complete;
3. reopen; and
4. complete again.

The final record is completed. Its local append-only history contains exactly
`created`, `completed`, `reopened`, and `completed` in order. The owner
reported **success**.

## Acceptance judgement

Milestone 68 passes Windows, browser, recovery, privacy, and owner acceptance.
The implementation is useful without Ollama, preserves explicit owner control,
does not invent work, and keeps permanent knowledge unchanged.
