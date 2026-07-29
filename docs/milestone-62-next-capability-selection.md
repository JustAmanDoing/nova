# Milestone 62 - Evidence-Led Next Capability Selection

**Completion date:** 30 July 2026

**Decision:** Complete; Milestone 63 selected, runtime implementation not yet
approved

## Objective

Choose one bounded capability after the accepted 0.59.0 daily-use beta. The
selection must improve practical value without weakening local-first privacy,
owner control, recoverability, or the modular-monolith architecture.

## Evidence used

- Milestone 61 found no release-blocking defect.
- The accepted chat and owner-approved personal-knowledge flow is stable.
- Chat cannot currently use intake documents.
- Existing intake already extracts and stores bounded local text.
- Existing deterministic search, source fingerprints, chat streaming, and
  citation presentation can be reused.
- The current runtime has one local Ollama model and more than 965 GB of free
  N-drive capacity.
- Remote access, voice, autonomous actions, semantic retrieval, plugins, and
  agents remain separate product and risk decisions.

## Selection method

Candidates were scored from 1 to 5, where 5 is strongest. The weighted score
uses:

- practical owner value: 30%;
- fit with current architecture: 20%;
- privacy and safety: 20%;
- reuse of verified NOVA components: 15%; and
- delivery and maintenance simplicity: 15%.

The score is a transparent comparison aid, not a claim of mathematical
certainty.

| Rank | Candidate | Value | Fit | Safety | Reuse | Delivery | Weighted |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Explicit local document context in chat | 5 | 5 | 4 | 5 | 4 | 4.65 |
| 2 | Project and goal workspace | 4 | 4 | 4 | 4 | 3 | 3.85 |
| 3 | Broad semantic document search | 5 | 3 | 3 | 2 | 2 | 3.30 |
| 4 | Secure phone access to NOVA | 4 | 2 | 2 | 3 | 2 | 2.75 |
| 5 | Voice conversation | 4 | 2 | 2 | 2 | 2 | 2.60 |
| 6 | User-controlled filing automation | 3 | 3 | 1 | 3 | 2 | 2.45 |

## Selected product slice

**Milestone 63 - Explicit Local Document Context**

The owner explicitly selects one currently indexed, ready intake document for
one chat turn. NOVA verifies the current source path and SHA-256, injects a
bounded copy of its already extracted text into the local model prompt, and
stores a visible `[D1]` citation with the completed assistant message.

This slice closes a demonstrated capability gap without adding embeddings,
automatic retrieval, document upload, another database, another service, or
external network access.

## Why the other candidates are later

### Project and goal workspace

Current owner-approved `goal` and `project` knowledge types already provide a
basic path. A separate workspace should wait until usage shows which planning
views and workflows are actually missing.

### Semantic document search

Meaning-based retrieval has high value, but it introduces embedding-model
selection, vector-index lifecycle, new retrieval-quality measures, and broader
implicit document access. Explicit selection provides a safer bridge and
creates evidence for whether semantic retrieval is needed.

### Secure phone access

The NOVA services are deliberately loopback-only. Remote access requires an
authentication, transport-security, session, origin, and threat-model
decision. It should not be bundled into document chat.

### Voice

Voice introduces microphone permission, local speech recognition, local
speech generation, interruption, retention, and mobile-access decisions. It
should build on a stable interaction and access boundary.

### Filing automation

The current approval and separate execution boundary is intentionally manual.
Automation requires measured recommendation accuracy and owner-defined rules;
the beta evidence does not justify relaxing that boundary.

## Decision boundary

Milestone 62 approves the product selection and its reviews only. It does not
authorize a database migration, API change, frontend change, runtime rebuild,
or version bump.

Milestone 63 implementation requires the owner's explicit approval of
`docs/milestone-63-explicit-document-context-proposal.md`.

## Completion estimate

- Guarded Intake MVP: 100%.
- Accepted practical local NOVA prototype scope: 100%.
- Broader long-term NOVA vision: approximately 76%.
- Milestone 62 decision work: 100%.

## Exact next action

Obtain explicit owner approval for Milestone 63. If approved, implement only
the bounded explicit-document slice, run architecture and engineering
acceptance, perform Windows owner testing, and issue a release-readiness
decision before beginning any other capability.
