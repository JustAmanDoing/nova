# Milestone 70 - Phone Daily-Use Validation

**Validation date:** 31 July 2026

**Release candidate:** 0.70.0

**Status:** Owner acceptance and protected implementation integration passed;
release evidence integration is pending

## Objective

Make the accepted private phone interface easier to use every day without
adding runtime authority, automatic actions, external services, or a new source
of truth.

The owner approved phone-first usability as the priority and asked NOVA to
become the go-to interface. The accepted message-composer behavior remains
unchanged: it stays within reach while the conversation scrolls, then stops at
the end of the chat section instead of covering knowledge controls.

## Evidence-led findings

The installed 0.69.0 release was inspected at a phone-sized viewport across
Intake, Chat, and Focus.

| Finding | Observed effect | Correction |
| --- | --- | --- |
| M70-U001 | Intake exceeded the phone content width because its service status competed with the primary navigation. | Hide the secondary status in the phone header and standardize the compact sticky navigation. |
| M70-U002 | Conversation history required a sideways scrollbar and made changing conversations awkward. | Use one labelled phone conversation picker while preserving the desktop history list. |
| M70-U003 | The genuine next-action form appeared after project and goal reference cards. | Put owner-entered next actions before reference information. |
| M70-U004 | Long technical boundary text interrupted the main daily journeys. | Keep the safeguards unchanged but place the full explanation behind clearly labelled optional details. |
| M70-U005 | Record-review links and navigation controls had small phone touch areas. | Raise the relevant touch targets to at least 44 pixels. |

## Candidate behavior

- Chat, Focus, and Intake remain the only primary destinations.
- Their phone navigation remains visible while the page scrolls.
- Chat exposes one compact conversation selector on phone and preserves the
  full conversation list on wider screens.
- Focus presents the owner's next action before project and goal reference
  cards. NOVA still does not infer priority, progress, deadlines, reminders, or
  additional work.
- Intake explains its main workflow in plain language. The deterministic filing
  and approval boundary remains available in the optional explanation.
- Backup, knowledge, and Focus boundary details remain present but do not crowd
  the primary journey.
- No data model, endpoint, permission, network listener, provider, or guarded
  action changed.

## Acceptance state

Automated, installed-runtime, phone-sized browser, desktop browser, and
physical-phone owner evidence has passed. The owner verified:

1. moving between Chat, Focus, and Intake while scrolled;
2. changing conversations with the phone picker;
3. sending a normal chat message with the accepted sticky composer;
4. viewing Focus and reaching Next actions before project and goal reference
   cards; and
5. optional explanations open and close without obscuring the main action.

No personal content is required for this acceptance check.

The accepted candidate was rebuilt as release 0.70.0. Direct backend,
same-origin frontend, and private tailnet HTTPS health all returned `ok` for
that exact version. Docker remained bound to Windows loopback, Tailscale Serve
remained tailnet-only, public Funnel remained off, SQLite integrity returned
`ok` at schema 16, and the operational status reported no warnings. A verified
post-acceptance backup was created as
`nova-20260731T113439.231344Z.db` with SHA-256
`60ae3bb0295d360573fa4055943828fb49cb55c74bbbafe046864a6646949ff3`.

## Release gate

Owner acceptance is satisfied. Protected PR #15 passed Backend quality,
Frontend quality, Windows controls, and Production runtime before merge commit
`4053f5b6a5a23efccf94e781fe2c8c3889d7ada0` entered `main`. The exact merged
`main` was then rebuilt and revalidated locally. Tag and publish 0.70.0 only
after the evidence-only release review passes. A failed check returns the
release to correction; it does not weaken an existing privacy or safety
boundary.

## Exact next milestone

After owner acceptance and release integration, begin **Milestone 71 -
Evidence-Led Next Capability Selection**. It is proposal and review work only;
no new runtime capability is pre-approved by this validation.
