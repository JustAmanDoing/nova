# Milestone 32: Windows-safe container checkout

## Outcome

Nova now preserves Linux container entrypoints with LF line endings even when
the repository is cloned on Windows with Git's automatic CRLF conversion
enabled.

## Root cause

The application source and Docker images built successfully, but a Windows
checkout converted `backend/docker-entrypoint.sh` to CRLF. Linux then read the
shebang as `/bin/sh\r` and reported the misleading error:

```text
exec /usr/local/bin/nova-entrypoint: no such file or directory
```

## Correction

- `.gitattributes` requires LF for shell scripts, Dockerfiles, and YAML.
- Native PowerShell and command launchers retain CRLF.
- The entrypoint is deliberately rewritten under the new attribute.
- Python and Windows-runner checks reject a CRLF container entrypoint.

## Verification

- Inspect the entrypoint bytes for `#!/bin/sh\n` and absence of CRLF.
- Run the Windows launcher-control check after GitHub checkout.
- Build and start the production containers from a Windows checkout.
- Verify the migrated API version, database integrity, and loopback-only ports.
