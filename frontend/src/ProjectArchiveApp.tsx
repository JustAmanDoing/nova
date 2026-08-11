import { useEffect, useMemo, useRef, useState } from "react";

import AppShell from "./AppShell";

import {
  getProjectArchive,
  getProjectArchiveDocument,
  type ProjectArchiveDocument,
  type ProjectArchiveReport,
  type ProjectArchiveSource,
} from "./lib/api";

const CATEGORY_LABELS: Record<string, string> = {
  current_status: "Current status",
  repository_snapshot: "Repository evidence",
  session: "Dated project sessions",
  legacy_archive: "Earlier development archive",
  project_snapshot: "Imported project snapshots",
  raw_chat_source: "Raw chat sources",
};

const AUTHORITY_LABELS: Record<string, string> = {
  authoritative_repository: "Authoritative repository",
  verified_runtime: "Verified runtime",
  approved_knowledge: "Approved knowledge",
  supporting_record: "Supporting local record",
  raw_unapproved: "Raw imported source · not approved knowledge",
};

export default function ProjectArchiveApp() {
  const [report, setReport] = useState<ProjectArchiveReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [document, setDocument] = useState<ProjectArchiveDocument | null>(null);
  const [documentLoading, setDocumentLoading] = useState(false);
  const closePreviewButton = useRef<HTMLButtonElement>(null);

  async function loadReport(signal?: AbortSignal, showLoading = true) {
    if (showLoading) setLoading(true);
    try {
      setReport(await getProjectArchive(signal));
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
    void getProjectArchive(controller.signal)
      .then((loadedReport) => {
        setReport(loadedReport);
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
    if (document) closePreviewButton.current?.focus();
  }, [document]);

  const groupedSources = useMemo(() => {
    const groups = new Map<string, ProjectArchiveSource[]>();
    for (const source of report?.sources ?? []) {
      groups.set(source.category, [...(groups.get(source.category) ?? []), source]);
    }
    return [...groups.entries()];
  }, [report]);

  async function openDocument(source: ProjectArchiveSource) {
    setDocumentLoading(true);
    try {
      setDocument(await getProjectArchiveDocument(source.id));
      setError(null);
    } catch (loadError: unknown) {
      setError(errorMessage(loadError));
    } finally {
      setDocumentLoading(false);
    }
  }

  return (
    <AppShell
      activeWorkspace="record"
      contentClassName="archive-shell"
      status={(
        <span className="archive-local-status">
          <span aria-hidden="true" />
          Local source record
        </span>
      )}
    >

      <header className="archive-hero">
        <div>
          <p className="eyebrow">Milestone 76 · Local NOVA Project Record</p>
          <h1>NOVA remembers its own project.</h1>
          <p>
            Current status, release evidence, approved records, and imported
            NOVA sources stay on this PC. Raw chat sources remain separate from
            approved knowledge.
          </p>
        </div>
        <button type="button" onClick={() => void loadReport()} disabled={loading}>
          {loading ? "Checking…" : "Refresh record"}
        </button>
      </header>

      {error ? <p className="archive-error" role="alert">{error}</p> : null}

      <section className="archive-summary" aria-label="Project record summary">
        <SummaryCard label="Current release" value={report?.current_release ?? "—"} />
        <SummaryCard
          label="Verified local sources"
          value={loading ? "—" : String(report?.verified_count ?? 0)}
        />
        <SummaryCard
          label="Raw chat sources supplied"
          value={loading ? "—" : String(report?.raw_chat_source_count ?? 0)}
        />
        <SummaryCard
          label="Changed or missing"
          value={
            loading
              ? "—"
              : String((report?.changed_count ?? 0) + (report?.missing_count ?? 0))
          }
        />
      </section>

      <section className="archive-migration">
        <div>
          <p className="section-number">Migration state</p>
          <h2>What is local now</h2>
        </div>
        <p>{report?.migration_summary ?? "Checking the local project record…"}</p>
        {report && report.raw_chat_source_count === 0 ? (
          <p className="archive-note">
            No raw ChatGPT conversation has been supplied yet. Repository,
            runtime, approved knowledge, and dated project records are local;
            ChatGPT chat history is not being claimed as migrated.
          </p>
        ) : null}
      </section>

      {report?.warnings.length ? (
        <section className="archive-warning" aria-label="Archive warnings">
          <h2>Needs attention</h2>
          <ul>{report.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>
        </section>
      ) : null}

      <div className="archive-layout">
        <section className="archive-sources">
          <div className="archive-section-heading">
            <div>
              <p className="section-number">Source catalogue</p>
              <h2>{report?.source_count ?? 0} local records</h2>
            </div>
          </div>
          {!loading && groupedSources.length === 0 ? (
            <p className="archive-empty">
              The archive is ready, but its first current-status index has not
              been generated yet.
            </p>
          ) : null}
          {groupedSources.map(([category, sources]) => (
            <section className="archive-group" key={category}>
              <h3>{CATEGORY_LABELS[category] ?? readable(category)}</h3>
              <div className="archive-source-list">
                {sources.map((source) => (
                  <article className="archive-source" key={source.id}>
                    <div>
                      <strong>{source.label}</strong>
                      <span>{AUTHORITY_LABELS[source.authority] ?? readable(source.authority)}</span>
                      <small>{source.relative_path}</small>
                    </div>
                    <div className="archive-source-action">
                      <span className={`archive-verification ${source.verification_status}`}>
                        {readable(source.verification_status)}
                      </span>
                      {source.preview_available ? (
                        <button
                          type="button"
                          onClick={() => void openDocument(source)}
                          disabled={documentLoading}
                        >
                          Open
                        </button>
                      ) : null}
                    </div>
                  </article>
                ))}
              </div>
            </section>
          ))}
        </section>

        <aside
          className={`archive-preview ${document ? "has-document" : ""}`}
          aria-label="Selected archive document"
          role={document ? "dialog" : undefined}
          aria-modal={document ? "true" : undefined}
          onKeyDown={(event) => {
            if (event.key === "Escape") setDocument(null);
          }}
        >
          <p className="section-number">Source preview</p>
          {document ? (
            <>
              <div className="archive-preview-heading">
                <h2>{document.label}</h2>
                <button
                  ref={closePreviewButton}
                  type="button"
                  onClick={() => setDocument(null)}
                >
                  Close
                </button>
              </div>
              <small>{document.relative_path} · SHA-256 {document.sha256.slice(0, 12)}…</small>
              {document.truncated ? (
                <p className="archive-note">Preview is bounded; the full source remains local.</p>
              ) : null}
              <pre>{document.content}</pre>
            </>
          ) : (
            <p>Select a verified text record to inspect its local source.</p>
          )}
        </aside>
      </div>
    </AppShell>
  );
}

function SummaryCard({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function readable(value: string): string {
  return value.replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase());
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Unable to read the local project record.";
}
