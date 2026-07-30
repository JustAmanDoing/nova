# Milestone 65 - Windows and Browser Acceptance

**Acceptance date:** 30 July 2026

**Release:** 0.65.0

**Implementation commit:** `d05e30f05232ac439a8313d438ba095fd5ceb57f`

**Merge commit:** `36e38dac18a24e06f0ff44104187bce1f243578c`

**Decision:** Pass

## Protected verification

PR #7 ran the complete required matrix against the exact implementation head:

- Backend quality — pass
- Frontend quality — pass
- Windows controls — pass
- Production runtime — pass

Run: `30530636149`

Merged `main` repeated the same four checks successfully.

Run: `30530714690`

## Local installation

- N-drive checkout fast-forwarded to merge commit `36e38dac`.
- The existing guarded update controller created a verified pre-update
  database backup.
- Backup:
  `nova-20260730T092809.516455Z.db`
- SHA-256:
  `707753947d7466a9acb879224cf13c26593da45f57cbdc8bacf0f6fb27257323`
- The database file and filename-bound sidecar matched.
- Containers rebuilt and started successfully.
- Backend and frontend remained published only on `127.0.0.1`.

## Runtime checks

| Check | Result |
| --- | --- |
| Health version | `0.65.0` |
| API health | Pass |
| Active database integrity | Pass |
| Operational warnings | None |
| Local free space | 897.9 GB, 96.4% |
| Planning endpoint | Pass |
| Active projects | 0, truthful empty state |
| Current goals | 0, truthful empty state |
| Unverified exclusions | 0 |
| Planning API `no-store` | Pass |
| Frontend CSP | Pass |
| `nosniff` | Pass |
| Frame denial | Pass |
| Unexpected frontend Host | Connection closed |
| Unexpected API Host | Rejected with 400 |
| Container errors | None |

No synthetic project or goal was added to the owner's permanent knowledge.

## Browser checks

The installed `/focus.html` page was inspected in the connected local browser.

Passed:

- correct title, navigation, headings, and read-only boundary;
- separate Active projects and Current goals regions;
- truthful empty-state wording;
- visible statement that NOVA does not invent priority, progress, deadlines, or
  next actions;
- read-only Refresh without error;
- **Add through chat** navigated to the guarded chat flow;
- the chat handoff prepared
  `Remember that my active project is `;
- the chat displayed
  `Prepared an editable prompt. Nothing has been sent or saved.`;
- no automatic send or permanent knowledge creation occurred;
- 390-pixel responsive viewport retained both sections and had no horizontal
  overflow;
- desktop and narrow layouts were visually coherent; and
- browser console warnings and errors were empty.

Native links and buttons received keyboard focus. The connected in-app browser
did not synthesize Enter navigation for the already-focused native link, so
keyboard activation evidence is supported by the native `<a href>` and
`<button>` implementation plus automated component tests rather than a
separate Windows key injection. This is a low residual acceptance limitation,
not a custom-keyboard implementation defect.

## Data-card limitation

The owner's current knowledge contains no active `project` or `goal`, so the
installed host could validate only the real empty state. Project and goal card
rendering, current/review-due state, revision display, retirement exclusion,
and integrity-failure exclusion passed automated backend and frontend tests.
Milestone 66 will validate cards with genuine owner-approved records rather
than inserting test data into permanent personal knowledge.

## Acceptance judgement

Milestone 65 is safe for release. The residual keyboard-tooling and real-card
limitations are documented and bounded. Neither weakens the local-first,
read-only, approval, integrity, privacy, or lifecycle boundaries.
