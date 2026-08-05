import { type FormEvent, useEffect, useState } from "react";

import {
  completeNextAction,
  createNextAction,
  getNextActions,
  getPlanningOverview,
  reopenNextAction,
  type NextAction,
  type NextActionOverview,
  type PlanningKnowledgeItem,
  type PlanningOverview,
} from "./lib/api";

function FocusApp() {
  const [overview, setOverview] = useState<PlanningOverview | null>(null);
  const [actions, setActions] = useState<NextActionOverview | null>(null);
  const [planningLoading, setPlanningLoading] = useState(true);
  const [actionsLoading, setActionsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [planningError, setPlanningError] = useState<string | null>(null);
  const [actionsError, setActionsError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    void loadPlanning(controller.signal);
    void loadActions(controller.signal);
    return () => controller.abort();

    async function loadPlanning(signal: AbortSignal) {
      try {
        const result = await getPlanningOverview(signal);
        if (signal.aborted) return;
        setOverview(result);
        setPlanningError(null);
      } catch (caught: unknown) {
        if (!isAbort(caught)) setPlanningError(errorMessage(caught));
      } finally {
        if (!signal.aborted) setPlanningLoading(false);
      }
    }

    async function loadActions(signal: AbortSignal) {
      try {
        const result = await getNextActions(signal);
        if (signal.aborted) return;
        setActions(result);
        setActionsError(null);
      } catch (caught: unknown) {
        if (!isAbort(caught)) setActionsError(errorMessage(caught));
      } finally {
        if (!signal.aborted) setActionsLoading(false);
      }
    }
  }, []);

  async function refresh() {
    setRefreshing(true);
    const [planningResult, actionResult] = await Promise.allSettled([
      getPlanningOverview(),
      getNextActions(),
    ]);
    if (planningResult.status === "fulfilled") {
      setOverview(planningResult.value);
      setPlanningError(null);
    } else {
      setPlanningError(errorMessage(planningResult.reason));
    }
    if (actionResult.status === "fulfilled") {
      setActions(actionResult.value);
      setActionsError(null);
    } else {
      setActionsError(errorMessage(actionResult.reason));
    }
    setRefreshing(false);
  }

  function applyActionChange(action: NextAction) {
    setActions((current) => {
      if (!current) return current;
      const withoutChanged = [...current.open, ...current.completed].filter(
        (item) => item.id !== action.id,
      );
      const open = withoutChanged
        .filter((item) => item.status === "open")
        .concat(action.status === "open" ? [action] : [])
        .sort(compareOpenActions);
      const completed = withoutChanged
        .filter((item) => item.status === "completed")
        .concat(action.status === "completed" ? [action] : [])
        .sort(compareCompletedActions);
      return {
        ...current,
        generated_at: new Date().toISOString(),
        open,
        completed,
      };
    });
    setActionsError(null);
  }

  const visibleCount =
    (overview?.projects.length ?? 0) + (overview?.goals.length ?? 0);
  const planningUnavailable = Boolean(planningError && !overview);

  return (
    <main className="focus-shell">
      <nav className="nav chat-nav" aria-label="Primary navigation">
        <a className="brand" href="/">
          <span className="brand-mark" aria-hidden="true">N</span>
          Nova
        </a>
        <div className="chat-nav-links">
          <a className="chat-nav-link" href="/chat.html">Chat</a>
          <a
            className="chat-nav-link active"
            href="/focus.html"
            aria-current="page"
          >
            Focus
          </a>
          <a className="chat-nav-link" href="/archive.html">Record</a>
          <a className="chat-nav-link" href="/librarian.html">Librarian</a>
          <a className="chat-nav-link" href="/">Intake</a>
        </div>
        <span className="focus-local-status">
          <span aria-hidden="true" />
          Local and owner controlled
        </span>
      </nav>

      <header className="focus-hero">
        <div>
          <p className="eyebrow">Milestone 68 · Owner-Approved Next Actions</p>
          <h1>Keep direction visible.</h1>
          <p>
            One calm view of the direction you approved and the next actions
            you explicitly entered. NOVA does not invent priorities, progress,
            deadlines, reminders, or additional work.
          </p>
        </div>
        <div className="focus-summary" aria-label="Focus overview">
          <span>Verified direction</span>
          <strong>{planningLoading || planningUnavailable ? "—" : visibleCount}</strong>
          <small>
            {planningUnavailable
              ? "Verification unavailable"
              : `${actions?.open.length ?? 0} open next actions`}
          </small>
          <button
            type="button"
            onClick={() => void refresh()}
            disabled={refreshing}
          >
            {refreshing ? "Checking…" : "Refresh"}
          </button>
        </div>
      </header>

      {planningError ? (
        <p className="focus-alert" role="alert">
          Projects and goals are unavailable. Existing knowledge was not
          changed. {planningError}
        </p>
      ) : null}

      {overview?.warning ? (
        <p className="focus-warning" role="status">{overview.warning}</p>
      ) : null}

      <NextActionsSection
        actions={actions}
        projects={overview?.projects ?? []}
        loading={actionsLoading}
        error={actionsError}
        onActionChanged={applyActionChange}
      />

      <div className="focus-grid" aria-busy={planningLoading}>
        <PlanningSection
          id="projects-title"
          eyebrow="Owner-approved direction"
          title="Active projects"
          items={overview?.projects ?? []}
          loading={planningLoading}
          unavailable={planningUnavailable}
          emptyMessage="No verified active project has been approved yet."
          addRequirement="active-projects"
        />
        <PlanningSection
          id="goals-title"
          eyebrow="Owner-approved outcomes"
          title="Current goals"
          items={overview?.goals ?? []}
          loading={planningLoading}
          unavailable={planningUnavailable}
          emptyMessage="No verified current goal has been approved yet."
          addRequirement="current-goals"
        />
      </div>

      <details className="focus-boundary">
        <summary>How Focus stays under your control</summary>
        <p>
          Knowledge changes still use NOVA’s review controls. Next actions are
          saved only when you submit the local form, and completion history is
          retained. {overview?.limitation} {actions?.limitation}
        </p>
      </details>
    </main>
  );
}

function PlanningSection({
  id,
  eyebrow,
  title,
  items,
  loading,
  unavailable,
  emptyMessage,
  addRequirement,
}: {
  id: string;
  eyebrow: string;
  title: string;
  items: PlanningKnowledgeItem[];
  loading: boolean;
  unavailable: boolean;
  emptyMessage: string;
  addRequirement: "active-projects" | "current-goals";
}) {
  return (
    <section className="focus-section" aria-labelledby={id}>
      <div className="focus-section-heading">
        <div>
          <p className="section-number">{eyebrow}</p>
          <h2 id={id}>{title}</h2>
        </div>
        <span>{items.length}</span>
      </div>
      {loading ? (
        <p className="focus-empty">Checking verified local knowledge…</p>
      ) : unavailable ? (
        <p className="focus-empty">
          Unable to verify this section right now. No knowledge was changed.
        </p>
      ) : items.length ? (
        <div className="focus-card-list">
          {items.map((item) => <PlanningCard key={item.id} item={item} />)}
        </div>
      ) : (
        <div className="focus-empty">
          <p>{emptyMessage}</p>
          <a href={`/chat.html?knowledge=${addRequirement}`}>
            Add through chat
          </a>
          <small>Nothing is saved until you approve the review card.</small>
        </div>
      )}
    </section>
  );
}

function PlanningCard({ item }: { item: PlanningKnowledgeItem }) {
  return (
    <article className="focus-card">
      <div className="focus-card-heading">
        <span className={`focus-review-state ${item.review_state}`}>
          {item.review_state === "review_due" ? "Review due" : "Current"}
        </span>
        <span>Revision {item.revision}</span>
      </div>
      <h3>{item.title}</h3>
      <p>{item.content}</p>
      <dl>
        <div>
          <dt>Updated</dt>
          <dd>{formatDate(item.updated_at)}</dd>
        </div>
        <div>
          <dt>{item.review_state === "review_due" ? "Due since" : "Review by"}</dt>
          <dd>{formatDate(item.review_due_at)}</dd>
        </div>
      </dl>
      <a href={`/chat.html?record=${encodeURIComponent(item.id)}`}>
        Review approved record
      </a>
    </article>
  );
}

function NextActionsSection({
  actions,
  projects,
  loading,
  error,
  onActionChanged,
}: {
  actions: NextActionOverview | null;
  projects: PlanningKnowledgeItem[];
  loading: boolean;
  error: string | null;
  onActionChanged: (action: NextAction) => void;
}) {
  const [title, setTitle] = useState("");
  const [projectRecordId, setProjectRecordId] = useState("");
  const [saving, setSaving] = useState(false);
  const [changingId, setChangingId] = useState<string | null>(null);
  const [mutationError, setMutationError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalized = title.trim();
    if (!normalized) {
      setMutationError("Enter a next action before saving.");
      return;
    }
    setSaving(true);
    setMutationError(null);
    setNotice(null);
    try {
      const created = await createNextAction({
        title: normalized,
        project_record_id: projectRecordId || null,
      });
      onActionChanged(created);
      setTitle("");
      setProjectRecordId("");
      setNotice("Next action added locally.");
    } catch (caught: unknown) {
      setMutationError(errorMessage(caught));
    } finally {
      setSaving(false);
    }
  }

  async function transition(action: NextAction, target: "complete" | "reopen") {
    setChangingId(action.id);
    setMutationError(null);
    setNotice(null);
    try {
      const changed = target === "complete"
        ? await completeNextAction(action.id)
        : await reopenNextAction(action.id);
      onActionChanged(changed);
      setNotice(
        target === "complete"
          ? "Next action marked complete. Its history was retained."
          : "Next action reopened.",
      );
    } catch (caught: unknown) {
      setMutationError(errorMessage(caught));
    } finally {
      setChangingId(null);
    }
  }

  const unavailable = Boolean(error && !actions);

  return (
    <section className="next-actions" aria-labelledby="next-actions-title">
      <div className="next-actions-heading">
        <div>
          <p className="section-number">Owner-entered work</p>
          <h2 id="next-actions-title">Next actions</h2>
        </div>
        <span>{actions?.open.length ?? 0} open</span>
      </div>

      <form className="next-action-form" onSubmit={(event) => void submit(event)}>
        <label>
          Next action
          <input
            type="text"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            maxLength={200}
            placeholder="Enter one concrete next action"
            disabled={saving}
          />
        </label>
        <label>
          Active project (optional)
          <select
            value={projectRecordId}
            onChange={(event) => setProjectRecordId(event.target.value)}
            disabled={saving || projects.length === 0}
          >
            <option value="">No project association</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.title} · revision {project.revision}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" disabled={saving}>
          {saving ? "Adding…" : "Add next action"}
        </button>
        <small>
          This saves only what you enter. NOVA will not add, rank, or schedule
          other actions.
        </small>
      </form>

      {mutationError ? (
        <p className="focus-alert" role="alert">{mutationError}</p>
      ) : null}
      {notice ? <p className="focus-notice" role="status">{notice}</p> : null}
      {error ? (
        <p className="focus-alert" role="alert">
          Next actions are unavailable. Existing actions were not changed. {error}
        </p>
      ) : null}

      {loading ? (
        <p className="next-actions-empty">Checking local next actions…</p>
      ) : unavailable ? (
        <p className="next-actions-empty">
          Unable to verify next actions right now. No actions were changed.
        </p>
      ) : actions?.open.length ? (
        <div className="next-action-list">
          {actions.open.map((action) => (
            <NextActionCard
              key={action.id}
              action={action}
              changing={changingId === action.id}
              onTransition={transition}
            />
          ))}
        </div>
      ) : (
        <p className="next-actions-empty">
          No open next actions. Add one only when it is genuinely useful.
        </p>
      )}

      {actions?.completed.length ? (
        <details className="completed-actions">
          <summary>Completed history ({actions.completed.length})</summary>
          <div className="next-action-list">
            {actions.completed.map((action) => (
              <NextActionCard
                key={action.id}
                action={action}
                changing={changingId === action.id}
                onTransition={transition}
              />
            ))}
          </div>
        </details>
      ) : null}
    </section>
  );
}

function NextActionCard({
  action,
  changing,
  onTransition,
}: {
  action: NextAction;
  changing: boolean;
  onTransition: (
    action: NextAction,
    target: "complete" | "reopen",
  ) => Promise<void>;
}) {
  const target = action.status === "open" ? "complete" : "reopen";
  return (
    <article className={`next-action-card ${action.status}`}>
      <div>
        <span>{action.status === "open" ? "Open" : "Completed"}</span>
        <h3>{action.title}</h3>
        {action.project_title ? (
          <p>
            Project: {action.project_title} · revision {action.project_revision}
          </p>
        ) : action.project_unavailable ? (
          <p>Project association unavailable; stale content is hidden.</p>
        ) : (
          <p>No project association</p>
        )}
      </div>
      <button
        type="button"
        disabled={changing}
        onClick={() => void onTransition(action, target)}
      >
        {changing
          ? "Saving…"
          : target === "complete"
            ? "Mark complete"
            : "Reopen"}
      </button>
    </article>
  );
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Date unavailable";
  return new Intl.DateTimeFormat("en-AU", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(date);
}

function compareOpenActions(left: NextAction, right: NextAction): number {
  return left.created_at.localeCompare(right.created_at) || left.id.localeCompare(right.id);
}

function compareCompletedActions(left: NextAction, right: NextAction): number {
  return (
    (right.completed_at ?? "").localeCompare(left.completed_at ?? "")
    || left.id.localeCompare(right.id)
  );
}

function isAbort(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Unable to load the local view.";
}

export default FocusApp;
