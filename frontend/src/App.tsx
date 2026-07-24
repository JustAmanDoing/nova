import { useCallback, useEffect, useState } from "react";

import {
  getHealth,
  getIntakeFiles,
  getIntakeSummary,
  scanIntake,
  type HealthResponse,
  type IntakeFilters,
  type IntakeFile,
  type IntakeSummary,
  type RecommendationRecord,
  type UnderstandingRecord,
} from "./lib/api";

type ServiceState =
  | { kind: "loading" }
  | { kind: "online"; health: HealthResponse }
  | { kind: "offline"; message: string };

function App() {
  const [service, setService] = useState<ServiceState>({ kind: "loading" });
  const [files, setFiles] = useState<IntakeFile[]>([]);
  const [summary, setSummary] = useState<IntakeSummary>({
    files_observed: 0,
    understood: 0,
    ready_for_review: 0,
    exact_duplicates: 0,
  });
  const [intakeError, setIntakeError] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [filters, setFilters] = useState<IntakeFilters>({});

  const loadIntake = useCallback(async (signal?: AbortSignal) => {
    try {
      const [nextFiles, nextSummary] = await Promise.all([
        getIntakeFiles(filters, signal),
        getIntakeSummary(signal),
      ]);
      setFiles(nextFiles);
      setSummary(nextSummary);
      setIntakeError(null);
    } catch (error: unknown) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      setIntakeError(error instanceof Error ? error.message : "Unable to load intake");
    }
  }, [filters]);

  useEffect(() => {
    const controller = new AbortController();

    getHealth(controller.signal)
      .then((health) => setService({ kind: "online", health }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        const message = error instanceof Error ? error.message : "Unknown error";
        setService({ kind: "offline", message });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const initialLoad = window.setTimeout(
      () => void loadIntake(controller.signal),
      200,
    );
    const refresh = window.setInterval(() => void loadIntake(), 5_000);
    return () => {
      controller.abort();
      window.clearTimeout(initialLoad);
      window.clearInterval(refresh);
    };
  }, [loadIntake]);

  async function handleScan() {
    setIsScanning(true);
    try {
      await scanIntake();
      await loadIntake();
    } catch (error: unknown) {
      setIntakeError(error instanceof Error ? error.message : "Scan failed");
    } finally {
      setIsScanning(false);
    }
  }

  return (
    <main className="shell">
      <nav className="nav" aria-label="Primary navigation">
        <a className="brand" href="/">
          <span className="brand-mark" aria-hidden="true">N</span>
          Nova
        </a>
        <div className="nav-status">
          <Status state={service} />
          <span className="phase">Intake MVP · 0.3.0</span>
        </div>
      </nav>

      <section className="hero">
        <div>
          <p className="eyebrow">Observe + understand + recommend · Files remain untouched</p>
          <h1>Turn incoming files into useful context.</h1>
          <p className="lede">
            Add a TXT, Markdown, PDF, or DOCX file to <code>data/intake</code>.
            Nova reads it locally, records what it understands, and applies
            deterministic filing rules when evidence is strong enough. Every
            recommendation is explainable and nothing is changed.
          </p>
        </div>
        <div className="safety-card">
          <span className="safety-icon" aria-hidden="true">✓</span>
          <div>
            <strong>Safe recommendations</strong>
            <p>Your intake folder stays read-only. Suggestions are displayed, never executed.</p>
          </div>
        </div>
      </section>

      <section className="workspace" aria-labelledby="intake-title">
        <div className="workspace-heading">
          <div>
            <p className="section-number">02–03 · Understand + recommend</p>
            <h2 id="intake-title">What Nova knows and recommends</h2>
          </div>
          <button type="button" onClick={handleScan} disabled={isScanning}>
            {isScanning ? "Scanning…" : "Scan now"}
          </button>
        </div>

        <div className="metrics" aria-label="Intake summary">
          <Metric label="Files observed" value={summary.files_observed} />
          <Metric label="Understood" value={summary.understood} />
          <Metric label="Ready for review" value={summary.ready_for_review} />
          <Metric
            label="Exact duplicates"
            value={summary.exact_duplicates}
            accent={summary.exact_duplicates > 0}
          />
        </div>

        <SearchControls filters={filters} onChange={setFilters} resultCount={files.length} />

        {intakeError ? <p className="error-banner">{intakeError}</p> : null}

        <div className="file-panel">
          {files.length === 0 && !intakeError ? (
            <div className="empty-state">
              <span aria-hidden="true">↓</span>
              <h3>Your intake is empty</h3>
              <p>Drop a TXT, Markdown, PDF, or DOCX file into <code>data/intake</code>.</p>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>File</th>
                    <th>Intake</th>
                    <th>Understanding</th>
                    <th>Evidence</th>
                    <th>Recommendation</th>
                    <th>Observed</th>
                  </tr>
                </thead>
                <tbody>
                  {files.map((file) => (
                    <tr key={file.id}>
                      <td>
                        <strong>{file.original_name}</strong>
                        <span>
                          {formatBytes(file.size_bytes)} · {file.sha256.slice(0, 12)}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${file.status}`}>
                          {file.status === "duplicate" ? "Duplicate" : "Observed"}
                        </span>
                      </td>
                      <td>
                        <UnderstandingBadge understanding={file.understanding} />
                      </td>
                      <td className="understanding-cell">
                        <strong>{understandingTitle(file.understanding)}</strong>
                        <span>{understandingDetail(file.understanding)}</span>
                      </td>
                      <td className="recommendation-cell">
                        <RecommendationView recommendation={file.recommendation} />
                      </td>
                      <td>{formatObserved(file.observed_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>
    </main>
  );
}

function RecommendationView({
  recommendation,
}: {
  recommendation: RecommendationRecord | null;
}) {
  if (!recommendation) {
    return (
      <>
        <span className="badge recommendation pending">Pending</span>
        <span>Nova has not evaluated this file yet.</span>
      </>
    );
  }
  if (recommendation.outcome === "insufficient_evidence") {
    return (
      <>
        <span className="badge recommendation insufficient">No recommendation</span>
        <span title={recommendation.reasons.join(" ")}>
          {recommendation.reasons[0]}
        </span>
      </>
    );
  }
  return (
    <>
      <span className="badge recommendation suggested">
        {recommendation.category} · {Math.round(recommendation.confidence * 100)}%
      </span>
      <strong>{recommendation.suggested_filename}</strong>
      <span>Destination: {recommendation.destination}</span>
      <span title={recommendation.reasons.join(" ")}>
        {recommendation.reasons[0]}
      </span>
    </>
  );
}

function UnderstandingBadge({
  understanding,
}: {
  understanding: UnderstandingRecord | null;
}) {
  const status = understanding?.status ?? "pending";
  return (
    <span className={`badge understanding ${status}`}>
      {understandingLabel(understanding)}
    </span>
  );
}

function understandingLabel(understanding: UnderstandingRecord | null): string {
  switch (understanding?.status) {
    case "ready":
      return "Understood";
    case "empty":
      return "Empty";
    case "unsupported":
      return "Not supported";
    case "too_large":
      return "Too large";
    case "failed":
      return "Needs attention";
    default:
      return "Pending";
  }
}

function understandingTitle(understanding: UnderstandingRecord | null): string {
  if (!understanding) return "Waiting for scan";
  if (understanding.title) return understanding.title;
  switch (understanding.status) {
    case "empty":
      return "Empty text file";
    case "unsupported":
      return "Format not supported yet";
    case "too_large":
      return "File exceeds the extraction limit";
    case "failed":
      return "Local extraction failed";
    default:
      return "Text extracted locally";
  }
}

function understandingDetail(understanding: UnderstandingRecord | null): string {
  if (!understanding) return "Nova has not processed this file yet.";
  if (understanding.error) {
    const code = understanding.error_code ? ` [${understanding.error_code}]` : "";
    const retry = understanding.retryable ? " Retry the scan after checking file access." : "";
    return `${understanding.error}${code} Extractor: ${understanding.extraction_method}.${retry}`;
  }
  if (understanding.text_preview) {
    const wordSummary =
      understanding.word_count === null ? "" : ` · ${understanding.word_count} words`;
    return `${understanding.text_preview}${wordSummary}`;
  }
  return understanding.evidence;
}

function SearchControls({
  filters,
  onChange,
  resultCount,
}: {
  filters: IntakeFilters;
  onChange: (filters: IntakeFilters) => void;
  resultCount: number;
}) {
  const hasFilters = Object.values(filters).some(Boolean);
  return (
    <section className="search-panel" aria-label="Search intake files">
      <label className="search-field">
        <span>Search files, extracted text, and recommendations</span>
        <input
          type="search"
          value={filters.query ?? ""}
          placeholder="Filename, content, evidence, category, destination, or error"
          onChange={(event) => onChange({ ...filters, query: event.target.value })}
        />
      </label>
      <div className="filter-row">
        <label>
          <span>Intake status</span>
          <select
            value={filters.status ?? ""}
            onChange={(event) =>
              onChange({
                ...filters,
                status: event.target.value as IntakeFilters["status"],
              })
            }
          >
            <option value="">All</option>
            <option value="observed">Observed</option>
            <option value="duplicate">Duplicate</option>
          </select>
        </label>
        <label>
          <span>Understanding</span>
          <select
            value={filters.understandingStatus ?? ""}
            onChange={(event) =>
              onChange({
                ...filters,
                understandingStatus:
                  event.target.value as IntakeFilters["understandingStatus"],
              })
            }
          >
            <option value="">All</option>
            <option value="ready">Understood</option>
            <option value="empty">Empty</option>
            <option value="unsupported">Not supported</option>
            <option value="too_large">Too large</option>
            <option value="failed">Needs attention</option>
          </select>
        </label>
        <label>
          <span>Extension</span>
          <input
            value={filters.extension ?? ""}
            placeholder="txt"
            onChange={(event) => onChange({ ...filters, extension: event.target.value })}
          />
        </label>
        <label>
          <span>Document type</span>
          <input
            value={filters.documentType ?? ""}
            placeholder="plain_text"
            onChange={(event) =>
              onChange({ ...filters, documentType: event.target.value })
            }
          />
        </label>
        <div className="search-summary">
          <span>{resultCount} result{resultCount === 1 ? "" : "s"}</span>
          <button
            type="button"
            className="secondary-button"
            disabled={!hasFilters}
            onClick={() => onChange({})}
          >
            Clear
          </button>
        </div>
      </div>
    </section>
  );
}

function Metric({
  label,
  value,
  accent = false,
}: {
  label: string;
  value: number;
  accent?: boolean;
}) {
  return (
    <article className={accent ? "metric accent" : "metric"}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function Status({ state }: { state: ServiceState }) {
  if (state.kind === "loading") {
    return <p className="status pending"><span />Checking API</p>;
  }
  if (state.kind === "offline") {
    return <p className="status offline" title={state.message}><span />API unavailable</p>;
  }
  return <p className="status online"><span />Nova online</p>;
}

function formatBytes(bytes: number): string {
  if (bytes < 1_024) return `${bytes} B`;
  if (bytes < 1_048_576) return `${(bytes / 1_024).toFixed(1)} KB`;
  return `${(bytes / 1_048_576).toFixed(1)} MB`;
}

function formatObserved(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default App;
