# Milestone 13 — User-controlled learning

## Outcome

Nova 0.13.0 makes confirmed destination learning visible and removable. Users
can inspect every stored document-type and category group, understand whether
its current evidence is eligible, and explicitly forget the group's derived
examples.

## Preference summary

The local API and dashboard report:

- Document type and base category.
- The leading destination, when there is no tie.
- Supporting and total active example counts.
- Total stored examples, including examples invalidated by undo.
- Preference share and current eligibility.
- The group's learning revision.

The summary does not expose source filenames, hashes, extracted text, or
document contents.

## Forget flow

The user selects **Forget examples** and types:

```text
FORGET <document type> / <category>
```

Nova rejects any non-exact confirmation. A successful reset:

1. Deletes all active and reverted derived examples in that group.
2. Advances only that group's learning revision.
3. Recalculates affected recommendations.
4. Records a minimal append-only reset event with the group and removed count.

The reset is transactional. A database failure leaves both the examples and
the group revision unchanged.

## Safety boundary

Forgetting learning does not rename, move, overwrite, delete, restore, or share
any document. It does not alter the append-only move/undo history. If removing
the preference changes an existing suggestion, its generation changes and it
returns to review rather than preserving stale approval.

Schema migration 10 adds the learning reset audit table. Existing databases are
upgraded in place through the ordered migration runner.
