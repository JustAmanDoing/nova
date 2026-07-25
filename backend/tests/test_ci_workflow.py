import re
from pathlib import Path

WORKFLOW_PATH = (
    Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"
)
IMMUTABLE_ACTION = re.compile(
    r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}\s+#\s+v[0-9][A-Za-z0-9_.-]*"
)


def test_external_ci_actions_use_immutable_commits() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    uses_values = [
        line.split("uses:", 1)[1].strip()
        for line in workflow.splitlines()
        if line.strip().startswith("uses:")
    ]
    external_actions = [value for value in uses_values if not value.startswith("./")]

    assert external_actions
    assert all(IMMUTABLE_ACTION.fullmatch(value) for value in external_actions)


def test_production_workflow_exercises_guarded_recovery_boundaries() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    for required_endpoint in (
        "/approval",
        "/execute",
        "/undo",
        "$api/backups",
        "/restore",
    ):
        assert required_endpoint in workflow
