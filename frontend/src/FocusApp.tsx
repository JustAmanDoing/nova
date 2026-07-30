import { useEffect, useState } from "react";

import {
  getPlanningOverview,
  type PlanningKnowledgeItem,
  type PlanningOverview,
} from "./lib/api";

function FocusApp() {
  const [overview, setOverview] = useState<PlanningOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getPlanningOverview(controller.signal)
      .then((result) => {
        if (controller.signal.aborted) return;
        setOverview(result);
        setError(null);
      })
      .catch((caught: unknown) => {
        if (caught instanceof DOMException && caught.name === "AbortError") return;
        setError(errorMessage(caught));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, []);

  async function refresh() {
    setRefreshing(true);
    try {
      const result = await getPlanningOverview();
      setOverview(result);
      setError(null);
    } catch (caught: unknown) {
      setError(errorMessage(caught));
    } finally {
      setRefreshing(false);
    }
  }

  const visibleCount =
    (overview?.projects.length ?? 0) + (overview?.goals.length ?? 0);
  const unavailable = Boolean(error && !overview);

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
          <a className="chat-nav-link" href="/">Intake</a>
        </div>
        <span className="focus-local-status">
          <span aria-hidden="true" />
          Verified local knowledge
        </span>
      </nav>

      <header className="focus-hero">
        <div>
          <p className="eyebrow">Milestone 65 · Active Projects &amp; Goals</p>
          <h1>Keep direction visible.</h1>
          <p>
            One calm view of the projects and goals you explicitly approved.
            NOVA displays verified knowledge; it does not invent priorities,
            progress, deadlines, or next actions.
          </p>
        </div>
        <div className="focus-summary" aria-label="Focus overview">
          <span>Verified active</span>
          <strong>{loading || unavailable ? "—" : visibleCount}</strong>
          <small>
            {unavailable
              ? "Verification unavailable"
              : overview?.excluded_unverified_count
              ? `${overview.excluded_unverified_count} safely excluded`
              : "No unverified records shown"}
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

      {error ? (
        <p className="focus-alert" role="alert">
          Projects and goals are unavailable. Existing knowledge was not
          changed. {error}
        </p>
      ) : null}

      {overview?.warning ? (
        <p className="focus-warning" role="status">{overview.warning}</p>
      ) : null}

      <div className="focus-grid" aria-busy={loading}>
        <PlanningSection
          id="projects-title"
          eyebrow="Owner-approved direction"
          title="Active projects"
          items={overview?.projects ?? []}
          loading={loading}
          unavailable={unavailable}
          emptyMessage="No verified active project has been approved yet."
          addRequirement="active-projects"
        />
        <PlanningSection
          id="goals-title"
          eyebrow="Owner-approved outcomes"
          title="Current goals"
          items={overview?.goals ?? []}
          loading={loading}
          unavailable={unavailable}
          emptyMessage="No verified current goal has been approved yet."
          addRequirement="current-goals"
        />
      </div>

      <footer className="focus-boundary">
        <strong>Read-only focus view.</strong>
        <span>
          Adding, correcting, and retiring knowledge continues through NOVA’s
          existing owner-review controls. {overview?.limitation}
        </span>
      </footer>
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

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Date unavailable";
  return new Intl.DateTimeFormat("en-AU", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(date);
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Unable to load the local view.";
}

export default FocusApp;
