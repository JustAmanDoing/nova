# Milestone 18: Production runtime smoke test

## Outcome

Nova's continuous verification now proves that the built production stack can
start and complete the first real workflow boundary. Building images alone is
no longer considered sufficient.

## Isolated check

The GitHub-hosted runner:

1. validates the Compose configuration
2. builds the backend and frontend production images
3. creates one synthetic text file under the runner's temporary intake folder
4. starts both services and waits for the backend health check
5. verifies the versioned health API
6. verifies the read-only operational-status API
7. verifies Nginx serves the compiled Nova dashboard
8. waits for the synthetic file to appear in the intake API
9. prints container state and logs when any step fails
10. always removes the isolated containers and database volume

No user documents, backups, database, Docker volumes, credentials, or
application secrets are present in the runner.

## Scope

The smoke test observes the synthetic file only. It does not approve, move,
undo, restore, delete, upload, or publish anything. Guarded file operations
remain covered by the backend integration tests and require explicit user
interaction in the product.
