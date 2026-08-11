import hashlib
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC

from app.services.chat import CapabilitySourceRecord
from app.services.knowledge import KnowledgeService, PlanningKnowledgeItemRecord
from app.services.librarian import LibrarianService
from app.services.next_actions import NextActionService
from app.services.project_archive import ProjectArchiveService

_MAX_ITEMS = 5
_NORMALIZE = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class ConductorCapabilityRecord:
    id: str
    label: str
    description: str
    prompt: str
    source_title: str
    source_url: str


@dataclass(frozen=True)
class ConductorResultRecord:
    content: str
    source: CapabilitySourceRecord


_CAPABILITIES = (
    ConductorCapabilityRecord(
        id="focus.next_actions",
        label="Open next actions",
        description="Show the owner's current open Next actions from Focus.",
        prompt="Show my open next actions",
        source_title="Focus",
        source_url="/focus.html#next-actions",
    ),
    ConductorCapabilityRecord(
        id="focus.projects_goals",
        label="Projects and goals",
        description="Show verified active projects and goals from Focus.",
        prompt="Show my projects and goals",
        source_title="Focus",
        source_url="/focus.html",
    ),
    ConductorCapabilityRecord(
        id="librarian.review",
        label="Librarian review",
        description="Show current knowledge health and the highest review items.",
        prompt="What needs review in Librarian?",
        source_title="Librarian",
        source_url="/librarian.html",
    ),
    ConductorCapabilityRecord(
        id="project_record.status",
        label="NOVA project status",
        description="Show the verified release and Project Record status.",
        prompt="Show NOVA project status",
        source_title="Project Record",
        source_url="/archive.html",
    ),
)


class ConductorService:
    def __init__(
        self,
        *,
        knowledge: KnowledgeService,
        librarian: LibrarianService,
        next_actions: NextActionService,
        project_archive: ProjectArchiveService,
    ) -> None:
        self.knowledge = knowledge
        self.librarian = librarian
        self.next_actions = next_actions
        self.project_archive = project_archive
        self._capabilities = {capability.id: capability for capability in _CAPABILITIES}
        self._routes = {
            _normalize(capability.prompt): capability.id
            for capability in _CAPABILITIES
        }

    def capabilities(self) -> tuple[ConductorCapabilityRecord, ...]:
        return _CAPABILITIES

    def match(self, content: str) -> str | None:
        return self._routes.get(_normalize(content))

    def execute(self, capability_id: str) -> ConductorResultRecord:
        capability = self._capabilities.get(capability_id)
        if capability is None:
            raise ValueError("The requested NOVA capability is not registered.")
        handlers = {
            "focus.next_actions": self._next_actions,
            "focus.projects_goals": self._projects_goals,
            "librarian.review": self._librarian_review,
            "project_record.status": self._project_status,
        }
        content, generated_at = handlers[capability_id]()
        return ConductorResultRecord(
            content=content,
            source=CapabilitySourceRecord(
                capability_id=capability.id,
                source_title=capability.source_title,
                source_url=capability.source_url,
                generated_at=generated_at,
                result_sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
            ),
        )

    def _next_actions(self) -> tuple[str, str]:
        overview = self.next_actions.overview()
        lines = ["Open next actions"]
        if not overview.open:
            lines.append("No open next actions are currently recorded.")
        else:
            for action in overview.open[:_MAX_ITEMS]:
                project = f" — {action.project_title}" if action.project_title else ""
                lines.append(f"- {action.title}{project}")
            hidden = len(overview.open) - _MAX_ITEMS
            if hidden > 0:
                lines.append(f"- {hidden} more open action{'s' if hidden != 1 else ''}")
        lines.append("Open Focus for the complete current list.")
        return "\n".join(lines), overview.generated_at

    def _projects_goals(self) -> tuple[str, str]:
        overview = self.knowledge.planning_overview()
        lines = ["Active projects and goals", "Projects:"]
        lines.extend(self._planning_lines(overview.projects))
        lines.append("Goals:")
        lines.extend(self._planning_lines(overview.goals))
        if overview.excluded_unverified_count:
            lines.append(
                f"{overview.excluded_unverified_count} unverified item"
                f"{'s were' if overview.excluded_unverified_count != 1 else ' was'} excluded."
            )
        if overview.warning:
            lines.append(overview.warning)
        lines.append("Open Focus to review the verified records.")
        return "\n".join(lines), overview.generated_at

    @staticmethod
    def _planning_lines(items: Sequence[PlanningKnowledgeItemRecord]) -> list[str]:
        if not items:
            return ["- None recorded"]
        lines: list[str] = []
        for item in items[:_MAX_ITEMS]:
            title = item.title
            review_state = item.review_state
            suffix = " — review due" if review_state == "review_due" else ""
            lines.append(f"- {title}{suffix}")
        hidden = len(items) - _MAX_ITEMS
        if hidden > 0:
            lines.append(f"- {hidden} more item{'s' if hidden != 1 else ''}")
        return lines

    def _librarian_review(self) -> tuple[str, str]:
        health = self.librarian.health()
        review = self.librarian.review()
        lines = [
            "Librarian review",
            f"Knowledge health: {health.health_score:g}/100",
            f"Current review items: {review.total}",
        ]
        if not review.issues:
            lines.append("No review item currently needs attention.")
        else:
            for issue in review.issues[:_MAX_ITEMS]:
                lines.append(f"- {issue.title} — {issue.summary}")
            hidden = len(review.issues) - _MAX_ITEMS
            if hidden > 0:
                lines.append(f"- {hidden} more review item{'s' if hidden != 1 else ''}")
        lines.append("Open Librarian for evidence and safe next steps.")
        return "\n".join(lines), review.generated_at

    def _project_status(self) -> tuple[str, str]:
        report = self.project_archive.report()
        release = report.current_release or "Not recorded"
        commit = report.current_commit or "Not recorded"
        lines = [
            "NOVA project status",
            f"Current release: {release}",
            f"Current commit: {commit}",
            f"Verified Project Record sources: {report.verified_count}/{report.source_count}",
        ]
        if report.changed_count or report.missing_count or report.invalid_count:
            lines.append(
                "Project Record attention: "
                f"{report.changed_count} changed, {report.missing_count} missing, "
                f"{report.invalid_count} invalid."
            )
        else:
            lines.append("Project Record has no changed, missing, or invalid source.")
        lines.append("Open Project Record for the complete evidence catalogue.")
        return "\n".join(lines), report.generated_at.astimezone(UTC).isoformat()


def _normalize(value: str) -> str:
    return " ".join(_NORMALIZE.sub(" ", value.casefold()).split())
