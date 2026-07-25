# Milestone 11 — Confirmed preference learning

## Outcome

Nova 0.11.0 learns one deliberately narrow preference: the destination used
for future filing suggestions. It learns only from successful, explicitly
approved moves and never converts a preference into an automatic action.

## Evidence threshold

A preference is eligible only when all of these conditions are true:

- The examples share the same extracted document type.
- Nova's proposed category was left unchanged by the user.
- At least three active successful moves support one destination.
- That destination represents at least 75% of the active examples.
- There is no tie for the strongest destination.

Until the threshold is met, the deterministic recommendation remains
unchanged.

## Reversibility

Each learning example is linked to the successful move operation that created
it. A successful undo marks that example as reverted. The relevant learning
revision advances, and existing suggestions in that document group are
recalculated. Duplicate event processing cannot add an example twice.

## Safety boundary

Learning changes only the suggested destination. It does not:

- Change the category or filename.
- Approve a recommendation.
- Move, rename, delete, share, or overwrite a file.
- Learn from a failed move, a pending approval, or a category correction.
- Use document groups other than the matching type and base category.

The dashboard explanation reports how many active examples support the
preference and states that explicit approval is still required. Execution
continues to require its separate confirmation and all existing fingerprint,
path, conflict, and no-overwrite checks.

## Persistence

Schema migration 9 adds:

- `learning_examples`, an operation-linked record of successful examples.
- `learning_state`, a per-document-type and category revision counter.
- `recommendation_results.learning_revision`, used to invalidate only affected
  cached recommendations.

The migration is ordered, recorded, and transactional. Existing databases are
upgraded in place without discarding intake, understanding, recommendation,
review, or operation history.
