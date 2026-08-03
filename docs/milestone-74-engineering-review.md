# Milestone 74 - Engineering Review

**Review date:** 3 August 2026

**Decision:** Pass with installed-model and owner acceptance required

## Implementation

- Replace the ambiguous restrictions-only Chat system prompt with concise,
  verified capability and boundary guidance.
- Keep the memory-approval and citation rules intact.
- Add an API-path regression test that captures the actual system message sent
  to the provider for the owner's exact improvement question.
- Bump backend and frontend release versions together to 0.74.0.

## Failure controls

- No private owner fact appears in the static prompt.
- Prompt tests must fail if capability guidance or precise action boundaries
  disappear.
- Full backend, frontend, Windows, Compose, production-runtime, backup,
  integrity, and private-network checks remain mandatory.
- A real local-model response and physical-owner review remain release gates;
  unit tests alone cannot prove response quality.

## Conclusion

The correction is bounded, reversible, and justified by direct daily-use
evidence. It may proceed without expanding NOVA's approved capability or
permission surface.
