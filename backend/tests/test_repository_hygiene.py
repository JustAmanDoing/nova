import subprocess
from fnmatch import fnmatch
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ALLOWED_SENSITIVE_NAMES = {".env.example"}
FORBIDDEN_TRACKED_PATTERNS = (
    "data/*",
    ".secrets/*",
    "*/.secrets/*",
    "secrets/*",
    "*/secrets/*",
    "credentials*.json",
    "*/credentials*.json",
    "*.db",
    "*.db-journal",
    "*.db-shm",
    "*.db-wal",
    "*.sqlite",
    "*.sqlite-journal",
    "*.sqlite-shm",
    "*.sqlite-wal",
    "*.sqlite3",
    "*.sqlite3-journal",
    "*.sqlite3-shm",
    "*.sqlite3-wal",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "id_rsa",
    "*/id_rsa",
    "id_dsa",
    "*/id_dsa",
    "id_ecdsa",
    "*/id_ecdsa",
    "id_ed25519",
    "*/id_ed25519",
)
REQUIRED_IGNORE_RULES = (
    ".env",
    ".env.*",
    "!.env.example",
    ".secrets/",
    "secrets/",
    "credentials*.json",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "data/",
    "*.db",
    "*.db-journal",
    "*.db-shm",
    "*.db-wal",
    "*.sqlite",
    "*.sqlite-journal",
    "*.sqlite-shm",
    "*.sqlite-wal",
    "*.sqlite3",
    "*.sqlite3-journal",
    "*.sqlite3-shm",
    "*.sqlite3-wal",
)


def test_sensitive_local_file_patterns_are_ignored() -> None:
    rules = {
        line.strip()
        for line in (REPOSITORY_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert set(REQUIRED_IGNORE_RULES) <= rules


def test_tracked_files_do_not_match_sensitive_local_patterns() -> None:
    result = subprocess.run(
        ["git", "-C", str(REPOSITORY_ROOT), "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    tracked = [
        path
        for path in result.stdout.decode("utf-8").split("\0")
        if path and path not in ALLOWED_SENSITIVE_NAMES
    ]
    forbidden = sorted(
        path
        for path in tracked
        if any(fnmatch(path.lower(), pattern) for pattern in FORBIDDEN_TRACKED_PATTERNS)
    )

    assert forbidden == []
