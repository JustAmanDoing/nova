# Milestone 30: Immutable CI actions

## Outcome

Nova's continuous-verification workflow no longer executes external actions
through movable major-version tags. Every external action is pinned to a
verified commit from its official GitHub repository.

## Pinned actions

- `actions/checkout` v6.1.0:
  `d23441a48e516b6c34aea4fa41551a30e30af803`
- `actions/setup-python` v6.3.0:
  `ece7cb06caefa5fff74198d8649806c4678c61a1`
- `actions/setup-node` v6.5.0:
  `249970729cb0ef3589644e2896645e5dc5ba9c38`

The readable release versions remain beside each commit in the workflow. A
repository test rejects future external action references that do not use a
40-character commit identifier and an accompanying version comment.

## Why this matters

A major-version tag can be moved after Nova's workflow has been reviewed.
Commit pinning ensures CI executes the reviewed source until the repository
deliberately adopts and validates another release.

## Verification

- Parse the workflow as YAML.
- Run the repository policy test.
- Run the full backend and frontend quality suites.
- Let GitHub Actions execute all Linux, Windows, and container jobs with the
  pinned references.

## Source releases

- [actions/checkout v6.1.0](https://github.com/actions/checkout/releases/tag/v6.1.0)
- [actions/setup-python v6.3.0](https://github.com/actions/setup-python/releases/tag/v6.3.0)
- [actions/setup-node v6.5.0](https://github.com/actions/setup-node/releases/tag/v6.5.0)
