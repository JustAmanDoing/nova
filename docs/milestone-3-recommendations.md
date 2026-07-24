# Milestone 3 — Deterministic Recommendations

## Outcome

Nova can now recommend filing details without AI and without changing any file.
Every observed file receives one of two outcomes:

- `suggested` when a deterministic rule has sufficient evidence
- `insufficient_evidence` when Nova should not guess

## Initial rules

| Rule | Minimum evidence | Category | Destination |
| --- | --- | --- | --- |
| Invoice | At least two invoice signals such as invoice, invoice number, supplier, or total | Financial | `Financial/Invoices` |
| Project | Project, roadmap, or milestone language | Project | `Project` |

Exact duplicates do not receive independent filing suggestions.

Suggested filenames use the approved convention:

```text
DD-MM-YYYY_Category_Subject_Source_v01.ext
```

## Safety boundary

- Rules operate only on locally extracted understanding records.
- Results include confidence and plain-language reasons.
- Weak evidence produces no recommendation.
- Recommendations are recalculated when file content, understanding results,
  duplicate status, or the rules version changes.
- The intake mount remains read-only.
- There are no approval, rename, move, delete, share, or automation controls.

## Acceptance examples

1. A complete invoice suggests the Financial category, an approved-format
   filename, and `Financial/Invoices`.
2. A project roadmap suggests the Project category and destination.
3. A general note returns `insufficient_evidence`.
4. An exact duplicate returns `insufficient_evidence`.
5. If the canonical copy is removed, the promoted remaining file is evaluated
   again.
6. Recommendation category, filename, destination, and reasons are searchable.
