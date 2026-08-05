# Milestone 77 - Local Project Record Daily-Use Validation

**Validation start:** 3 August 2026

**Validated release:** 0.76.1

**Status:** In progress; private-phone release checkpoint accepted

## Objective

Validate the accepted local Project Record during ordinary PC and phone use
before selecting another runtime capability. This milestone is validation and
documentation only. It does not add runtime authority, automatic import,
semantic search, an external provider, or another source of truth.

## Checkpoint 1 - Latest private-phone release

The owner requested the latest NOVA release on the phone and explicitly
reported that the result passed.

Independent verification immediately before owner acceptance confirmed:

- local `HEAD`, `origin/main`, tag `v0.76.1`, and the latest published GitHub
  release all identify release commit
  `29e6b092077db672a7cdd36bb691b3afc0d25c4e`;
- the installed local API, same-origin frontend API, and private Tailscale API
  all reported healthy NOVA `0.76.1`;
- the private Chat page returned HTTP 200 with `Cache-Control: no-cache`;
- the private browser route loaded **Chat with Nova**, reported **Local AI
  ready**, exposed local model `qwen3:8b`, and produced no browser warning or
  error entries;
- Docker exposed NOVA only on Windows loopback;
- Tailscale Serve remained tailnet-only at
  `https://nova.tail1d0293.ts.net`; and
- the PC and the owner's iPhone were both present in the same private tailnet.

The live Project Record reported 422 sources, all 422 verified, with zero
changed, missing, or invalid sources, zero warnings, and zero explicitly
supplied raw ChatGPT chat sources.

## Privacy and authority boundary

No source was imported for this checkpoint. NOVA still has no automatic access
to the owner's ChatGPT account, browser history, clipboard, or unrelated chat
content. Raw chat evidence remains separate from approved knowledge, and
permanent knowledge still requires the existing owner review and approval
workflow.

## Remaining daily-use evidence

Milestone 77 is not complete from this checkpoint alone. The remaining bounded
validation is:

1. use Record naturally on both PC and phone over ordinary daily work;
2. confirm the canonical project summary stays understandable and current;
3. if the owner has a genuine NOVA-only source worth preserving, exercise one
   guarded import and confirm its authority label and preview are clear; and
4. record catalogue growth, preview usefulness, and any import friction before
   selecting another capability.

A synthetic or unrelated source must not be imported merely to complete the
checklist. If no genuine source is available, record that boundary rather than
adding unnecessary personal data.

## Current decision

The private-phone release checkpoint passes with no observed release-blocking,
privacy, integrity, or usability defect. Release 0.76.1 remains installed and
published. Milestone 77 remains the active milestone until the remaining
daily-use evidence is recorded.

## Exact next action

Use the Record page during normal phone and PC work, then report one genuine
point of friction or confirm that the current summary, catalogue, and preview
remain useful. No new runtime capability is approved by this checkpoint.
