# Milestone 79 - Knowledge Examples Phase 1 Acceptance

**Acceptance date:** 9 August 2026

**Accepted source:** protected `main` merge
`93daa9806590c950c94044e637a44125f5739ec0`

**Accepted candidate:** `fc1cfb05a272cf99cd878b7ddacd146e88083c3a`
from PR #35

**Installed application version:** 0.78.2

**Status:** Integrated, installed, and owner-accepted on PC and phone

## Accepted behavior

Every one of NOVA's 13 knowledge checks provides two short, static examples of
useful information the owner could choose to add. The examples are optional
blank-page guidance, not facts, and NOVA never sends or saves one
automatically.

Examples appear only for missing information in Chat or after a missing
Librarian check is opened. Each example can prepare an editable Chat draft;
the existing generic handoff remains available. The normal explicit message
send and knowledge approval steps remain unchanged.

The accepted copy includes the **Home jobs and routines** name, privacy cautions
where relevant, and a clear statement that NOVA can remember time-based home
and vehicle information but cannot send reminders yet.

## Integration and installation evidence

- All four protected checks passed on candidate commit
  `fc1cfb05a272cf99cd878b7ddacd146e88083c3a`.
- PR #35 merged through protected `main` as
  `93daa9806590c950c94044e637a44125f5739ec0`.
- The guarded Windows updater created verified pre-update backup
  `nova-20260809T112647.273761Z.db` before downloading source changes.
- The backup's independently checked SHA-256 is
  `9e80e53bf18afa1718a27a87525fa245e1d1a7442e9275abe1c695409a92aa53`.
- The live checkout fast-forwarded cleanly to the exact protected-main merge,
  rebuilt both production images, recreated both services, and returned
  healthy version 0.78.2 with no operational warning.
- Direct backend, same-origin PC, and private Tailscale health requests all
  returned healthy version 0.78.2.
- The backend main process remained unprivileged, both published ports remained
  loopback-only, and Tailscale Funnel remained off.
- The active SQLite database passed its read-only quick check.
- The database SHA-256 remained
  `323fa850c14cbbcbe53ce93f6a015d96e7ca862484e315f5745dad9cd5372d2e`
  before and after installation and UI validation.
- Every database table count remained unchanged, including 23 conversations,
  243 messages, and 17 knowledge records. No action or approval record was
  created by example-draft validation.
- All 19 approved-knowledge files remained unchanged, with aggregate manifest
  SHA-256
  `98b301495c671de2382c576982a90e96877f59e60fda0aa0b782e248938306f4`.
- The installed API returned 13 requirements with two examples each. The four
  live missing-coverage issues each carried two examples.
- Installed desktop review confirmed missing-only visibility, the required
  label, 44-pixel example links, the preserved generic handoff, and an editable
  Chat draft with the explicit unsent and unsaved status.
- The exact candidate passed a 390-by-844 synthetic review before merge. After
  installation the private-phone endpoint remained healthy, and the owner
  explicitly accepted the behavior on both the physical PC and phone.
- Compose validation, runtime security headers, and the post-install log scan
  passed with no application error match.

No release tag or version bump was created for this backward-compatible Phase
1 change. Installation did not add a migration, dependency, service, network
path, model, permission, or external provider.

## Preserved boundaries and remaining limitations

- Examples remain static and curated, not personalised, generated, ranked, or
  learned from owner behavior.
- NOVA still cannot send reminders or notifications from this guidance.
- No Ignore or dismiss feature was added.
- Detection, scoring, priority, issue order, matching, and authority are
  unchanged.
- The pre-existing narrow-screen Chat header overflow remains outside this
  bounded correction.
- The private Tailscale route remains healthy and Funnel remains off, but the
  pre-existing NOVA ownership record for the current Serve configuration is
  still absent.
- PR #33 remained separate validation and state evidence until it merged at
  `41adbfff8c0bc44b091ff977e7635abc82e399ce`. It did not modify the accepted
  Phase 1 behavior.

## Project state

- Knowledge Examples Phase 1: 100 percent implemented, integrated, installed,
  and owner-accepted.
- Accepted practical local NOVA prototype: 100 percent.
- Broader long-term NOVA vision: approximately 86 percent.
- Milestone 79 overall: 100 percent; its separate daily-use validation evidence
  is integrated and the installed behavior is owner-accepted.

## Exact next action

Begin a separate evidence-led capability discussion. No Milestone 80 runtime
scope is approved before architecture review, engineering review, and explicit
owner approval.
