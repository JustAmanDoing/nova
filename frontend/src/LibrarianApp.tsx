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
  duplicate: "Duplicate",
  conflict: "Conflict",
  stale: "Review due",
  missing_coverage: "Missing coverage",
  missing_file: "Missing file",
  checksum_mismatch: "Checksum",
  broken_reference: "Broken reference",
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
          Read-only analysis
        </span>
      </nav>

      <header className="librarian-hero">
        <div>
          <p className="eyebrow">Milestone 78 · Knowledge health</p>
          <h1>Keep knowledge trustworthy.</h1>
          <p>
            The Librarian checks approved local records, sources, revisions,
            freshness, and checksums. It explains what needs review and changes
            nothing by itself.
          </p>
        </div>
        <button type="button" onClick={() => void load()} disabled={loading}>
          {loading ? "Checking…" : "Refresh analysis"}
        </button>
      </header>

      {error ? <p className="librarian-error" role="alert">{error}</p> : null}

      <section className="librarian-summary" aria-label="Knowledge health summary">
        <SummaryCard
          label="Knowledge health"
          value={loading && !health ? "—" : `${health?.health_score ?? 0}%`}
          tone="good"
        />
        <SummaryCard
          label="Review queue"
          value={loading && !review ? "—" : String(review?.total ?? 0)}
        />
        <SummaryCard
          label="Needs attention"
          value={loading && !health ? "—" : String(attentionCount)}
          tone={attentionCount > 0 ? "warn" : "good"}
        />
        <SummaryCard
          label="Verified sources"
          value={loading && !health ? "—" : String(health?.verified_source_count ?? 0)}
        />
      </section>

      <section className="librarian-method">
        <div>
          <p className="section-number">Five transparent checks</p>
          <h2>Health dimensions</h2>
        </div>
        <div className="librarian-dimensions">
          {Object.entries(health?.dimensions ?? {}).map(([label, value]) => (
            <div key={label}>
              <span>{readable(label)}</span>
              <strong>{value}%</strong>
              <div className="librarian-meter" aria-label={`${readable(label)} ${value}%`}>
                <span style={{ width: `${value}%` }} />
              </div>
            </div>
          ))}
          {!health ? <p>Checking the existing quality report and local sources…</p> : null}
        </div>
      </section>

      <div className="librarian-layout">
        <section className="librarian-queue" aria-label="Librarian review queue">
          <div className="librarian-section-heading">
            <div>
              <p className="section-number">Owner review</p>
              <h2>{review?.total ?? 0} items to consider</h2>
            </div>
            <span>No automatic changes</span>
          </div>
          {!loading && review?.issues.length === 0 ? (
            <p className="librarian-empty">No deterministic review item is active.</p>
          ) : null}
          <div className="librarian-issue-list">
            {review?.issues.map((issue) => (
              <article className="librarian-issue" key={issue.id}>
                <div className="librarian-issue-copy">
                  <div className="librarian-badges">
                    <span className={`librarian-priority ${issue.priority}`}>
                      {readable(issue.priority)}
                    </span>
                    <span>{ISSUE_LABELS[issue.issue_type]}</span>
                    <span>{Math.round(issue.confidence * 100)}% evidence</span>
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
                    View evidence
                  </button>
                  {issue.review_url ? <a href={issue.review_url}>Review</a> : null}
                </div>
              </article>
            ))}
          </div>
        </section>

        <aside
          className={`librarian-detail ${detail ? "has-detail" : ""}`}
          aria-label="Selected Librarian item"
          role={detail ? "dialog" : undefined}
          aria-modal={detail ? "true" : undefined}
          onKeyDown={(event) => {
            if (event.key === "Escape") setDetail(null);
          }}
        >
          <p className="section-number">Evidence and sources</p>
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
              <h3>Suggested next step</h3>
              <p>{detail.issue.suggested_action}</p>
              {detail.sources.map((source) => (
                <article className="librarian-source" key={source.record_id}>
                  <strong>{source.title}</strong>
                  <span>
                    {readable(source.kind)} · revision {source.revision} ·{" "}
                    {Math.round(source.candidate_confidence * 100)}% source confidence
                  </span>
                  <span>{readable(source.verification_status)}</span>
                  <p>{source.content}</p>
                  <small>{source.relative_path} · SHA-256 {source.sha256.slice(0, 12)}…</small>
                </article>
              ))}
              {detail.events.length ? (
                <>
                  <h3>Audit history</h3>
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
                  Open existing review workflow
                </a>
              ) : null}
            </>
          ) : (
            <p>Select a review item to inspect why it was flagged, its source
              confidence, and its immutable revision evidence.</p>
          )}
        </aside>
      </div>

      <footer className="librarian-boundary">
        <strong>The Librarian is advisory.</strong>
        <p>{health?.limitation ?? "It never edits, merges, retires, or deletes knowledge."}</p>
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
  return error instanceof Error ? error.message : "Unable to read Librarian analysis.";
}
