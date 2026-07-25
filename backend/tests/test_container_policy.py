import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DOCKERFILES = (
    REPOSITORY_ROOT / "backend" / "Dockerfile",
    REPOSITORY_ROOT / "frontend" / "Dockerfile",
)
FROM_LINE = re.compile(
    r"^FROM\s+(?P<reference>\S+)(?:\s+AS\s+\w+)?$",
    flags=re.IGNORECASE,
)
PINNED_REFERENCE = re.compile(
    r"^[^@\s]+@sha256:[0-9a-f]{64}$",
)


def test_every_container_base_image_is_pinned_by_digest() -> None:
    references: list[str] = []

    for dockerfile in DOCKERFILES:
        from_lines = [
            line.strip()
            for line in dockerfile.read_text(encoding="utf-8").splitlines()
            if line.strip().upper().startswith("FROM ")
        ]
        assert from_lines, f"{dockerfile} does not declare a base image"

        for line in from_lines:
            match = FROM_LINE.fullmatch(line)
            assert match is not None, f"Could not parse base image line: {line}"
            reference = match.group("reference")
            assert PINNED_REFERENCE.fullmatch(reference), (
                f"Base image must retain a readable tag and an immutable digest: {reference}"
            )
            readable_name = reference.split("@", maxsplit=1)[0].rsplit("/", maxsplit=1)[-1]
            assert ":" in readable_name, f"Base image tag is missing: {reference}"
            references.append(reference)

    assert len(references) == 3
