# NOVA Engineering Continuity

**Established:** 10 August 2026

**Scope:** development governance and read-only verification; no NOVA runtime
or Milestone 80 product behavior changes

## Canonical shared status

NOVA has one active status record:

`https://github.com/JustAmanDoing/nova/blob/project-status/STATUS.md`

It lives on the dedicated `project-status` branch so a session can publish its
handoff immediately without pretending that unmerged feature work is on
`main`, modifying product code, or waiting for a product pull request to merge.
Every status update is still a Git commit with reviewable history.

Repository code, commits, tags, pull requests, CI, and verified runtime evidence
remain authoritative for their respective facts. `STATUS.md` is the canonical
cross-device index of those facts. It must never override contradictory
evidence.

Historical milestone and release documents remain evidence. Chat memory,
ChatGPT project mirrors, exports, archives, installed project-record packages,
and local tracking refs are not current-status sources.

## Startup and resume workflow

Every ChatGPT, Codex Remote, PC, or phone-controlled NOVA engineering session
must complete this gate before status claims or engineering work:

1. Fetch `STATUS.md` from GitHub's `project-status` branch, not a local cached
   copy.
2. Confirm `verification: VERIFIED`, the verification timestamp, all required
   fields and sections, and the exact next action.
3. Resolve the named integrated and active branches and confirm their exact
   commit SHAs.
4. Resolve the named pull request when present; confirm state, draft status,
   base branch, head branch, and exact head SHA. Check exact-head CI separately.
5. Inspect the actual local checkout before local changes. A clean checkout may
   still be stale or on the wrong branch.
6. Verify tags/releases and physical runtime evidence before claiming a release
   is published, installed, healthy, or accepted.
7. Continue only when the record and current evidence reconcile.

On Windows, the standard read-only gate is:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Test-NovaContinuity.ps1
```

The script uses GitHub's public read-only API for this public repository. It
does not require the local GitHub CLI credential, mutate the checkout, or alter
NOVA. It validates the record schema, required sections, branch SHAs, and PR
head/base state. Exact CI, release publication, local checkout, and runtime
claims still require their named evidence because no single API response proves
all of them.

If GitHub is unavailable, a required ref or PR does not resolve, the record is
marked unverified, or evidence conflicts, stop and report:

`CURRENT STATUS NOT VERIFIED`

Do not fall back to memory or stale files and do not start feature work.

## End-of-session workflow

Every session that inspects, changes, verifies, reviews, merges, releases,
installs, accepts, or blocks NOVA work must update the same canonical record
before completion:

1. Reconcile the final repository and external evidence.
2. Replace, rather than append to, the active facts in `STATUS.md`.
3. Include current milestone, completed work, exact checks/tests, integrated and
   active branches, exact commits, PR and exact-head CI state, release/install/
   acceptance state, blockers/risks, and one executable next action.
4. Set `verification: UNVERIFIED` whenever the required facts cannot be proven.
5. Commit only the status change on `project-status` with a clear message such
   as `Update canonical NOVA status after continuity setup`.
6. Push the branch and read the file back from GitHub. Run the continuity check
   against the published record.

Do not create another active status issue, document, or branch. Milestone and
release evidence documents may be added normally, but they must point back to
the canonical record for the current handoff.

## Authority and change boundaries

- `main` is the canonical integrated code line.
- Feature branches and pull requests are authoritative for proposed code.
- GitHub Actions proves only the exact commit and jobs it ran.
- GitHub releases and tags prove publication, not installation.
- The guarded Windows installation and physical PC/phone checks prove installed
  runtime state and owner acceptance.
- `project-status/STATUS.md` is the canonical shared resume record that links
  those sources together.

Passing the continuity gate does not authorize a merge, release, installation,
scope expansion, data mutation, network change, dependency, provider, plugin,
agent, or autonomous action. Existing owner approvals and NOVA's development
playbook continue to govern those actions.
