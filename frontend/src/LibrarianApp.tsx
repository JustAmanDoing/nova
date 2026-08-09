import { useEffect, useMemo, useRef, useState } from "react";

import {
  getLibrarianHealth,
  getLibrarianItem,
  getLibrarianReview,
  type LibrarianHealth,
  type LibrarianIssue,
  type LibrarianItem,
  type LibrarianReview,
} from "./lib/api";

const ISSUE_LABELS: Record<string, string> = {
  duplicate: "Possible repeat",
  conflict: "Different versions",
  stale: "May need checking",
  missing_coverage: "Not saved yet",
  missing_file: "File missing",
  checksum_mismatch: "File changed",
  broken_reference: "File link problem",
};

const PRIORITY_LABELS: Record<string, string> = {
  critical: "Urgent",
  high: "Important",
  medium: "Worth checking",
  low: "Optional",
};

const DIMENSION_LABELS: Record<string, string> = {
  coverage: "What is saved",
  freshness: "Up to date",
  retrieval: "Easy to find",
  integrity: "Files match",
  consistency: "No conflicts",
};

const VERIFICATION_LABELS: Record<string, string> = {
  verified: "File checked",
  missing_file: "File missing",
  checksum_mismatch: "File changed",
  broken_reference: "File link problem",
};

export default function LibrarianApp() {
  const [health, setHealth] = useState<LibrarianHealth | null>(null);
  const [review, setReview] = useState<LibrarianReview | null>(null);
  const [detail, setDetail] = useState<LibrarianItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const closeButton = useRef<HTMLButtonElement>(null);

  async function load(signal?: AbortSignal, showLoading = true) {
    if (showLoading) setLoading(true);
    try {
      const [nextHealth, nextReview] = await Promise.all([
        getLibrarianHealth(signal),
        getLibrarianReview(signal),
      ]);
      setHealth(nextHealth);
      setReview(nextReview);
      setError(null);
    } catch (loadError: unknown) {
      if (loadError instanceof DOMException && loadError.name === "AbortError") return;
      setError(errorMessage(loadError));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const controller = new AbortController();
    void Promise.all([
      getLibrarianHealth(controller.signal),
      getLibrarianReview(controller.signal),
    ])
      .then(([nextHealth, nextReview]) => {
        setHealth(nextHealth);
        setReview(nextReview);
        setError(null);
      })
      .catch((loadError: unknown) => {
        if (loadError instanceof DOMException && loadError.name === "AbortError") return;
        setError(errorMessage(loadError));
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (detail) closeButton.current?.focus();
  }, [detail]);

  const attentionCount = useMemo(
    () =>
      (health?.counts.missing_files ?? 0) +
      (health?.counts.checksum_failures ?? 0) +
      (health?.counts.broken_references ?? 0) +
      (health?.counts.conflicts ?? 0),
    [health],
  );
  const itemCount = review?.total ?? 0;

  async function openItem(issue: LibrarianIssue) {
    setDetailLoading(true);
    try {
      setDetail(await getLibrarianItem(issue.id));
      setError(null);
    } catch (loadError: unknown) {
      setError(errorMessage(loadError));
    } finally {
      setDetailLoading(false);
    }
  }

  return (
    <main className="librarian-shell">
      <nav className="nav chat-nav" aria-label="Primary navigation">
        <a className="brand" href="/">
          <span className="brand-mark" aria-hidden="true">N</span>
          Nova
        </a>
        <div className="chat-nav-links">
          <a className="chat-nav-link" href="/chat.html">Chat</a>
          <a className="chat-nav-link" href="/focus.html">Focus</a>
          <a className="chat-nav-link" href="/archive.html">Record</a>
          <a
            className="chat-nav-link active"
            href="/librarian.html"
            aria-current="page"
          >
            Librarian
          </a>
          <a className="chat-nav-link" href="/">Intake</a>
        </div>
        <span className="librarian-local-status">
          <span aria-hidden="true" />
          Suggestions only
        </span>
      </nav>

      <header className="librarian-hero">
        <div>
          <p className="eyebrow">Knowledge check</p>
          <h1>Check what Nova remembers.</h1>
          <p>
            The Librarian checks your saved information and points out anything
            worth looking at. It never changes anything by itself.
          </p>
        </div>
        <button type="button" onClick={() => void load()} disabled={loading}>
          {loading ? "Checking…" : "Check again"}
        </button>
      </header>

      {error ? <p className="librarian-error" role="alert">{error}</p> : null}

      <section className="librarian-summary" aria-label="Knowledge health summary">
        <SummaryCard
          label="Overall health"
          value={loading && !health ? "—" : `${health?.health_score ?? 0}%`}
          tone="good"
        />
        <SummaryCard
          label="Suggestions"
          value={loading && !review ? "—" : String(review?.total ?? 0)}
        />
        <SummaryCard
          label="Problems"
          value={loading && !health ? "—" : String(attentionCount)}
          tone={attentionCount > 0 ? "warn" : "good"}
        />
        <SummaryCard
          label="Checked records"
          value={loading && !health ? "—" : String(health?.verified_source_count ?? 0)}
        />
      </section>

      <section className="librarian-method">
        <div>
          <p className="section-number">Five simple checks</p>
          <h2>How everything looks</h2>
        </div>
        <div className="librarian-dimensions">
          {Object.entries(health?.dimensions ?? {}).map(([label, value]) => (
            <div key={label}>
              <span>{DIMENSION_LABELS[label] ?? readable(label)}</span>
              <strong>{value}%</strong>
              <div
                className="librarian-meter"
                aria-label={`${DIMENSION_LABELS[label] ?? readable(label)} ${value}%`}
              >
                <span style={{ width: `${value}%` }} />
              </div>
            </div>
          ))}
          {!health ? <p>Checking your saved information…</p> : null}
        </div>
      </section>

      <div className="librarian-layout">
        <section className="librarian-queue" aria-label="Librarian review queue">
          <div className="librarian-section-heading">
            <div>
              <p className="section-number">Your choice</p>
              <h2>{itemCount} {itemCount === 1 ? "item" : "items"} to consider</h2>
            </div>
            <span>Nothing changes unless you choose</span>
          </div>
          {!loading && review?.issues.length === 0 ? (
            <p className="librarian-empty">Nothing needs your review.</p>
          ) : null}
          <div className="librarian-issue-list">
            {review?.issues.map((issue) => (
              <article className="librarian-issue" key={issue.id}>
                <div className="librarian-issue-copy">
                  <div className="librarian-badges">
                    <span className={`librarian-priority ${issue.priority}`}>
                      {PRIORITY_LABELS[issue.priority] ?? readable(issue.priority)}
                    </span>
                    <span>{ISSUE_LABELS[issue.issue_type]}</span>
                    <span>{Math.round(issue.confidence * 100)}% sure</span>
                  </div>
                  <h3>{issue.title}</h3>
                  <p>{issue.summary}</p>
                </div>
                <div className="librarian-actions">
                  <button
                    type="button"
                    onClick={() => void openItem(issue)}
                    disabled={detailLoading}
                  >
                    Why this is here
                  </button>
                  {issue.review_url ? <a href={issue.review_url}>Open</a> : null}
                </div>
              </article>
            ))}
          </div>
        </section>

        <aside
          className={`librarian-detail ${detail ? "has-detail" : ""}`}
          aria-label="Suggestion details"
          role={detail ? "dialog" : undefined}
          aria-modal={detail ? "true" : undefined}
          onKeyDown={(event) => {
            if (event.key === "Escape") setDetail(null);
          }}
        >
          <p className="section-number">Why this is here</p>
          {detail ? (
            <>
              <div className="librarian-detail-heading">
                <h2>{detail.issue.title}</h2>
                <button ref={closeButton} type="button" onClick={() => setDetail(null)}>
                  Close
                </button>
              </div>
              <p>{detail.issue.reason}</p>
              <ul>{detail.issue.evidence.map((item) => <li key={item}>{item}</li>)}</ul>
              <h3>What you can do</h3>
              <p>{detail.issue.suggested_action}</p>
              {detail.sources.map((source) => (
                <article className="librarian-source" key={source.record_id}>
                  <strong>{source.title}</strong>
                  <span>
                    Saved as {readable(source.kind).toLowerCase()} · version{" "}
                    {source.revision} · {Math.round(source.candidate_confidence * 100)}% sure
                  </span>
                  <span>
                    {VERIFICATION_LABELS[source.verification_status] ??
                      readable(source.verification_status)}
                  </span>
                  <p>{source.content}</p>
                  <small>
                    {source.relative_path} · File check code {source.sha256.slice(0, 12)}…
                  </small>
                </article>
              ))}
              {detail.events.length ? (
                <>
                  <h3>Change history</h3>
                  <ul>
                    {detail.events.map((event) => (
                      <li key={event.sequence}>
                        {readable(event.event_type)} · {event.detail}
                      </li>
                    ))}
                  </ul>
                </>
              ) : null}
              {detail.issue.review_url ? (
                <a className="librarian-review-link" href={detail.issue.review_url}>
                  Open review in Chat
                </a>
              ) : null}
            </>
          ) : (
            <p>
              Choose an item to see why Nova showed it, what information it used,
              and what you can do next.
            </p>
          )}
        </aside>
      </div>

      <footer className="librarian-boundary">
        <strong>The Librarian only makes suggestions.</strong>
        <p>{health?.limitation ?? "It never changes or removes your saved information."}</p>
      </footer>
    </main>
  );
}

function SummaryCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "good" | "warn";
}) {
  return (
    <div className={tone ? `is-${tone}` : undefined}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function readable(value: string): string {
  return value.replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase());
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Nova could not load this check.";
}
