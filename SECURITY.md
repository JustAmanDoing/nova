# Security policy

## Supported code

Nova is under active development. Security fixes apply to the latest commit on
the `main` branch; older local checkouts are not maintained separately.

## Report a vulnerability

Use GitHub's
[private vulnerability reporting](https://github.com/JustAmanDoing/nova/security/advisories/new)
for a suspected security issue. Include a concise description, affected
version, reproduction steps, and impact. Do not include personal documents,
database contents, credentials, API keys, or other secrets.

Do not open a public issue for an unpatched vulnerability or exposed secret.
If a credential is ever committed, revoke or rotate it immediately; deleting
the file in a later commit does not remove it from Git history.

## Local security boundary

Nova is designed for one trusted user on one Windows PC. Its dashboard and API
bind to IPv4 loopback only and do not provide multi-user authentication.
Changing the network binding or publishing the local ports requires a separate
security review.

The following remain private local data and must not be committed:

- `.env` files and credentials;
- private keys and certificates containing private keys;
- the `data/` directory;
- SQLite databases, backup snapshots, and checksum sidecars;
- source documents and extracted document text.

The repository includes ignore rules and an automated tracked-file policy test
for common sensitive filename patterns. These controls reduce accidental
commits but do not replace reviewing each change before publishing it.
