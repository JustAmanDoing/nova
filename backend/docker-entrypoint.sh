#!/bin/sh
# This entrypoint must retain LF line endings for its Linux shebang.
set -eu

# Bind-mounted folders can have host-specific ownership. Initialize only Nova's
# own directories as root, then immediately drop privileges for the application.
for directory in /data /files/intake /files/library /files/backups; do
    mkdir -p "$directory"
    chown nova:nova "$directory"
done

exec gosu nova "$@"
