# Milestone 49 — Filename-bound backup checksums

## Outcome

Nova now accepts a backup checksum sidecar only when it contains one valid
SHA-256 record bound to the exact backup filename.

## Integrity boundary

Nova writes checksum files in this form:

```text
<64 lowercase hexadecimal characters>  <exact backup filename>
```

Inventory listing treats the checksum as unavailable when the sidecar:

- omits the filename;
- names a different backup;
- contains extra records;
- contains non-ASCII data; or
- cannot be read.

The backup itself remains visible in recovery history, but Nova does not offer
it as verified recovery material. Download and restore continue to refuse it
until a valid filename-bound sidecar is present.

## Why this matters

A checksum value alone can establish content identity, but a portable sidecar
also needs to identify which file it describes. Enforcing both fields prevents
a copied, truncated, malformed, or mismatched sidecar from being represented
as a usable recovery record.

## Verification

Tests cover missing, hash-only, wrong-filename, multi-record, and non-ASCII
sidecars. Every malformed form remains listable as unverified while guarded
download and restore verification reject it.
