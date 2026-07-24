import { useCallback, useEffect, useMemo, useState } from "react";

import {
  getHealth,
  getIntakeFiles,
  scanIntake,
  type HealthResponse,
  type IntakeFile,
} from "./lib/api";

type ServiceState =
  | { kind: "loading" }
  | { kind: "online"; health: HealthResponse }
  | { kind: "offline"; message: string };

function App() {
  const [service, setService] = useState<ServiceState>({ kind: "loading" });
  const [files, setFiles] = useState<IntakeFile[]>([]);
  const [intakeError, setIntakeError] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);

  const loadFiles = useCallback(async (signal?: AbortSignal) => {
    try {
      const nextFiles = await getIntakeFiles(signal);
      setFiles(nextFiles);
      setIntakeError(null);
    } catch (error: unknown) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      setIntakeError(error instanceof Error ? error.message : "Unable to load intake");
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    getHealth(controller.signal)
      .then((health) => setService({ kind: "online", health }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        const message = error instanceof Error ? error.message : "Unknown error";
        setService({ kind: "offline", message });
      });
    void loadFiles(controller.signal);

    const refresh = window.setInterval(() => void loadFiles(), 5_000);
    return () => {
      controller.abort();
      window.clearInterval(refresh);
    };
  }, [loadFiles]);

  const duplicates = useMemo(
    () => files.filter((file) => file.status === "duplicate").length,
    [files],
  );

  async function handleScan() {
    setIsScanning(true);
    try {
      await scanIntake();
      await loadFiles();
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
          <span className="phase">Intake MVP · 0.1.0</span>
        </div>
      </nav>

      <section className="hero">
        <div>
          <p className="eyebrow">Observe first · Never move files silently</p>
          <h1>A safe landing place for every file.</h1>
          <p className="lede">
            Add a file to <code>data/intake</code>. Nova records its metadata,
            creates a SHA-256 fingerprint, and flags exact duplicates without
            renaming, moving, or deleting anything.
          </p>
        </div>
        <div className="safety-card">
          <span className="safety-icon" aria-hidden="true">✓</span>
          <div>
            <strong>Observation mode</strong>
            <p>Your intake folder is mounted read-only inside Nova.</p>
          </div>
        </div>
      </section>

      <section className="workspace" aria-labelledby="intake-title">
        <div className="workspace-heading">
          <div>
            <p className="section-number">01 · Intake</p>
            <h2 id="intake-title">Files Nova has observed</h2>
          </div>
          <button type="button" onClick={handleScan} disabled={isScanning}>
            {isScanning ? "Scanning…" : "Scan now"}
          </button>
        </div>

        <div className="metrics" aria-label="Intake summary">
          <Metric label="Files observed" value={files.length} />
          <Metric label="Ready for review" value={files.length - duplicates} />
          <Metric label="Exact duplicates" value={duplicates} accent={duplicates > 0} />
        </div>

        {intakeError ? <p className="error-banner">{intakeError}</p> : null}

        <div className="file-panel">
          {files.length === 0 && !intakeError ? (
            <div className="empty-state">
              <span aria-hidden="true">↓</span>
              <h3>Your intake is empty</h3>
              <p>Drop a file into <code>data/intake</code>, then select Scan now.</p>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>File</th>
                    <th>Status</th>
                    <th>Size</th>
                    <th>Fingerprint</th>
                    <th>Observed</th>
                  </tr>
                </thead>
                <tbody>
                  {files.map((file) => (
                    <tr key={file.id}>
                      <td>
                        <strong>{file.original_name}</strong>
                        <span>{file.relative_path}</span>
                      </td>
                      <td>
                        <span className={`badge ${file.status}`}>
                          {file.status === "duplicate" ? "Duplicate" : "Observed"}
                        </span>
                      </td>
                      <td>{formatBytes(file.size_bytes)}</td>
                      <td><code>{file.sha256.slice(0, 12)}</code></td>
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
