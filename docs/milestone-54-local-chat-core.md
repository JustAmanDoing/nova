# Milestone 54 — Local Chat Core

**Acceptance date:** 28 July 2026

**Base commit:** `72a4441` (accepted Milestone 53)

**Working branch:** `agent/milestone-54-local-chat-core`

**Prototype release:** 0.54.0

**Decision:** Passed; the local conversational prototype is working

## Scope delivered

- Discover locally installed Ollama models.
- Stream local-model replies as newline-delimited events.
- Create, list, open, and continue local conversations.
- Persist complete user and assistant messages in Nova's SQLite database.
- Stop an in-progress generation.
- Explain provider failure without inventing an assistant reply.
- Provide a responsive, dedicated `/chat.html` interface.
- Link the chat and existing intake interfaces without replacing either one.

## Architecture and safety boundaries

The existing modular monolith remains intact. A small Nova-owned provider
adapter communicates with Ollama's local HTTP API. The provider is replaceable
and does not make Open WebUI or another full application part of Nova's
codebase.

Database migration 11 adds `chat_conversations` and `chat_messages`. Chat
history is local derived application state and is covered by the existing
integrity-checked backup workflow.

Conversation creation and message submission require
`X-Nova-Intent: local-user-action`. Docker continues to publish the API and
frontend only on IPv4 loopback. Milestone 54 adds no tools, web access, RAG,
document access, autonomous actions, or permanent personal-memory promotion.
The intake workflow remains usable when Ollama is unavailable.

## Verification evidence

### Automated matrix

- Ruff passed.
- Strict mypy passed for 28 application source files.
- 106 backend tests passed with 92.29% total coverage.
- ESLint and TypeScript passed.
- 25 frontend tests passed, including four focused chat tests.
- Multi-page production frontend build passed.
- Windows launcher and controller structural validation passed.
- `git diff --check` passed.

### Production runtime

- Production backend and frontend container builds passed.
- Both services started healthy in isolated Compose project `nova-m54`.
- Health reported release `0.54.0`.
- Database integrity reported `ok` with schema migration 11.
- Model discovery returned `qwen3:8b` with its local model metadata.
- The chat page and both API services remained loopback-only.
- An isolated backend configured with an unreachable provider returned HTTP
  `503` from model discovery as designed.

### Real local-model acceptance

- A cold Qwen turn streamed the exact reply `NOVA PROTOTYPE READY`, persisted
  both messages, and completed in 107.56 seconds; first output arrived at
  107.40 seconds.
- With the model resident in GPU memory, the exact reply
  `WARM RESPONSE READY` began in 1.98 seconds and completed in 2.13 seconds.
- `ollama ps` reported `qwen3:8b` at 100% GPU with a 4096-token context.
- The browser sent and displayed the exact reply `BROWSER CHAT READY`.
- Stop worked both before generation began and during an active long reply.
  No partial assistant message was stored.
- With Ollama stopped, the browser showed `Local AI unavailable`, disabled new
  messages, and kept the saved eight-message conversation readable. After
  Ollama restarted, model discovery and the composer recovered.
- Live Stop testing exposed a stale conversation-count defect. The UI now
  refreshes both conversation content and the history summary after a stop or
  provider error; a regression test covers the correction.

### Browser and recovery acceptance

- The chat interface exposed semantic navigation, model selection, labelled
  input, conversation controls, and a live status notice.
- At 800 px and 560 px, the layout collapsed without horizontal overflow.
- A verified database backup passed SQLite integrity, recorded schema 11, and
  contained the accepted local conversation and its eight persisted messages.

## Known limitations

- A cold Qwen load from the current N: storage took approximately 108 seconds.
  Warm responses were fast, and Ollama is configured to keep the model loaded
  for 30 minutes. This is a performance limitation, not an API/UI delay.
- Chat is local to this PC in this milestone. Remote access and authentication
  are not part of this acceptance.
- Conversation rename and deletion are not implemented.
- Replies are displayed as safe plain text; rich Markdown and code rendering
  are deferred.
- Chat does not yet access documents or permanent personal knowledge.
- Voice, tools, web access, and autonomous actions remain deferred.

## Release-readiness decision

Milestone 54 passes prototype acceptance. The implementation is bounded,
local-first, architecture-preserving, tested against the real installed model,
and leaves the existing guarded intake system operational. The prototype is
available at:

`http://localhost:5173/chat.html`

## Exact next milestone

Milestone 55 — Conversation-to-Knowledge Capture is the next proposed product
slice. It must preserve explicit owner approval and must not silently promote
ordinary conversation into permanent personal knowledge. Runtime work has not
started.
