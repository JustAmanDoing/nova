# Milestone 65 - Architecture Review

**Review date:** 30 July 2026

**Review scope:** Implemented Active Projects and Goals Workspace

**Decision:** Pass for protected integration; Windows-host acceptance remains
required before release

## Source-of-truth review

The implementation creates no second project or task store. The existing
approved knowledge lifecycle remains authoritative:

```text
approved SQLite record
  + current no-overwrite Markdown revision
  + live path containment
  + live SHA-256 verification
        |
        v
read-only projects/goals projection
        |
        v
local Focus page
```

All writes still pass through the existing chat proposal, owner review,
immutable revision, and guarded retirement controls.

## Architecture findings

### Local-first and privacy-first

- The projection is produced by the existing local FastAPI service.
- The page is served by the existing loopback-only frontend.
- No cloud, upload, telemetry, external provider, or new network path is added.
- Unverifiable content is excluded rather than returned from stale database
  content.

### Owner control

- Viewing Focus changes no state.
- Selecting **Add through chat** only prepares editable text.
- Permanent storage still requires the owner to send the text and separately
  choose **Approve & save**.
- Updates and retirement reuse existing guarded lifecycle controls.

### Modular monolith

- One bounded service projection, one versioned route, and one focused
  frontend entry are added inside the existing application.
- No service split, event bus, plugin surface, agent framework, or duplicate
  database is introduced.
- No dependency is added.

### AI optionality

- The Focus projection, verification, review-state calculation, and display
  are deterministic.
- Ollama is not required to view approved projects and goals.
- AI is used only later if the owner chooses to continue through chat.

### Reversibility and auditability

- The milestone adds no direct write path.
- Existing immutable revisions, retirement events, database backups, and
  knowledge snapshots remain unchanged.

## Scope review

The implementation does not contain task management, inferred completion,
priority selection, scheduling, deadlines, reminders, autonomous updates,
semantic retrieval, remote access, voice, plugins, agents, tools, web access,
or external providers.

## Risks and controls

| Risk | Control |
| --- | --- |
| Stale content appears current | Fixed 90-day state labels verified records as **Review due** |
| Tampered or missing Markdown is exposed | Live path and SHA-256 verification; failed records are excluded |
| Focus becomes a second write path | All actions route to existing chat and lifecycle controls |
| Interface overstates planning intelligence | Explicit no-inference language and no generated planning fields |
| Local personal direction leaks | Existing loopback-only HTTP and private API boundaries remain |

## Architecture judgement

The implementation preserves the approved local-first, privacy-first,
owner-controlled modular monolith. Architecture approval is granted for
protected integration. Final release approval remains conditional on the
complete automated matrix and Windows-host acceptance.
