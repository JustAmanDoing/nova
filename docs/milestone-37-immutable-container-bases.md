# Milestone 37: Immutable container bases

## Outcome

Nova 0.37.0 pins every production Docker base image to the exact verified OCI
image-index digest used by the successful Windows and Linux builds.

## Pinned bases

- Python 3.12 slim for the API runtime;
- Node 20 Alpine for the dashboard build;
- Nginx 1.27 Alpine for the dashboard runtime.

Each Dockerfile retains the readable release tag and adds a 64-character
SHA-256 digest. The tag communicates intent while the digest prevents a future
registry tag change from silently altering an old Nova commit.

## Validation

The recorded digests were resolved with Docker Buildx and matched the identities
already reported by Nova's successful production builds. An automated policy
test parses every `FROM` instruction and rejects:

- an unpinned base;
- a malformed digest;
- a digest without a readable release tag;
- an unexpected change in the number of production base images.

GitHub's production workflow then builds and runs the pinned images through the
full intake, approval, execution, audit, undo, backup, and restore exercise.

## Maintenance

Digest pins deliberately prevent automatic base-image drift. Updating a base
requires resolving and reviewing a new digest, running the complete verification
workflow, and publishing the change as an intentional security update.

Operating-system packages installed during the backend build still come from
the repositories configured by the pinned Debian base. This milestone fixes
base-image identity; it does not claim byte-for-byte reproducibility of external
package repositories.
