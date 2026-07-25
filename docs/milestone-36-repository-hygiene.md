# Milestone 36: Public repository hygiene

## Outcome

Nova 0.36.0 adds repository-level controls for the most likely accidental
disclosure paths in a public source repository.

## Controls

- `.gitignore` excludes environment files, secret folders, credential exports,
  private-key containers, SQLite databases, and common SQLite journal files.
- `.env.example` remains intentionally tracked as a safe configuration
  template.
- `SECURITY.md` directs vulnerability reports to GitHub's private reporting
  channel and documents Nova's single-user, loopback-only security boundary.
- An automated test reads Git's tracked file list and rejects common sensitive
  local filename patterns. It separately verifies that the required ignore
  rules remain present.

## Boundary

Filename controls cannot determine whether ordinary source or documentation
text contains a secret. Every commit still requires review, and any exposed
credential must be revoked or rotated even when the file is later removed from
Git.

Nova data, backups, source documents, and extracted text remain private local
data and are not suitable for the public repository.
