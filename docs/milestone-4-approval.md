# Milestone 4 — Approval Boundary

## Outcome

Nova can now record how the user reviews a deterministic recommendation:

- **Approve** records acceptance of the current reviewed values.
- **Edit** stores corrected category, filename, and destination values while
  keeping the item awaiting review.
- **Reject** records that the recommendation should not be used.
- **Ignore** dismisses it without treating it as an accepted decision.
- **Review again** returns a decided item to the pending state.

These actions update local SQLite state only. No source file operation exists in
this milestone.

## Version binding

Every review stores the generation timestamp of the recommendation it applies
to. The API only returns a review when that timestamp matches the current
recommendation. If file content, understanding, duplicate status, or rules
change, the new recommendation has no current review and returns to the queue.

## Validation

Edited fields must satisfy the following before they are stored:

- Category is not empty.
- Suggested filename is not empty and contains no unsafe Windows filename
  characters or path separators.
- Destination is a non-empty relative folder path.
- Destination contains no parent traversal, drive prefix, or unsafe path
  component.

Execution will validate these values again when that separate boundary is
introduced.

## Explicit non-goals

- No rename or move
- No deletion
- No automatic approval
- No action audit presented as complete
- No undo claim
- No chatbot or AI decision layer

## Acceptance cases

1. Editing changes the reviewed values but not the source file.
2. Approving after an edit preserves the edited values.
3. Approve, reject, and ignore remove the item from the ready-for-review count.
4. Review again returns the item to pending.
5. A changed recommendation invalidates the earlier review.
6. Unsafe filenames and destination traversal are rejected.
