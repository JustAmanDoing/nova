import {
  type FormEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import AppShell from "./AppShell";

import {
  backupChecksumDownloadUrl,
  backupDownloadUrl,
  createDatabaseBackup,
  executeApproved,
  getActionHistory,
  getBackups,
  getHealth,
  getIntakeFiles,
  getLearningPreferences,
  getOperationalStatus,
  getRecoveryAssessments,
  getIntakeSummary,
  resetLearningPreference,
  restoreDatabaseBackup,
  reviewRecommendation,
  scanIntake,
  undoAction,
  type ActionRecord,
  type ApprovalRecord,
  type ApprovalRequest,
  type BackupRecord,
  type HealthResponse,
  type IntakeFilters,
  type IntakeFile,
  type IntakeSummary,
  type LearningPreferenceRecord,
  type OperationalStatus,
  type RecommendationRecord,
  type RecoveryAssessment,
  type RecoveryState,
  type UnderstandingRecord,
} from "./lib/api";

type ServiceState =
  | { kind: "loading" }
  | { kind: "online"; health: HealthResponse }
  | { kind: "offline"; message: string };

const BACKUP_REFRESH_INTERVAL_MS = 60_000;

function isAbortedResult(result: PromiseSettledResult<unknown>): boolean {
  return (
    result.status === "rejected" &&
    result.reason instanceof DOMException &&
    result.reason.name === "AbortError"
  );
}

function resultError(
  label: string,
  result: PromiseSettledResult<unknown>,
): string | null {
  if (result.status === "fulfilled") return null;
  const message =
    result.reason instanceof Error ? result.reason.message : "Request failed";
  return `${label}: ${message}`;
}

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
  const [filesUnavailable, setFilesUnavailable] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [reviewingFileId, setReviewingFileId] = useState<string | null>(null);
  const [actingId, setActingId] = useState<string | null>(null);
  const [actions, setActions] = useState<ActionRecord[]>([]);
  const [recoveries, setRecoveries] = useState<RecoveryAssessment[]>([]);
  const [backups, setBackups] = useState<BackupRecord[]>([]);
  const [preferences, setPreferences] = useState<LearningPreferenceRecord[]>([]);
  const [operations, setOperations] = useState<OperationalStatus | null>(null);
  const [isBackingUp, setIsBackingUp] = useState(false);
  const [restoringFilename, setRestoringFilename] = useState<string | null>(null);
  const [resettingPreference, setResettingPreference] = useState<string | null>(
    null,
  );
  const [backupNotice, setBackupNotice] = useState<string | null>(null);
  const [learningNotice, setLearningNotice] = useState<string | null>(null);
  const [filters, setFilters] = useState<IntakeFilters>({});
  const latestLoadRequest = useRef(0);

  const loadIntake = useCallback(async (
    signal?: AbortSignal,
    includeBackups = true,
  ): Promise<boolean> => {
    const requestId = latestLoadRequest.current + 1;
    latestLoadRequest.current = requestId;
    try {
      const backupRequest: Promise<BackupRecord[] | null> = includeBackups
        ? getBackups(signal)
        : Promise.resolve(null);
      const [
        healthResult,
        filesResult,
        summaryResult,
        actionsResult,
        recoveriesResult,
        backupResult,
        preferencesResult,
        operationsResult,
      ] = await Promise.allSettled([
        getHealth(signal),
        getIntakeFiles(filters, signal),
        getIntakeSummary(signal),
        getActionHistory(signal),
        getRecoveryAssessments(signal),
        backupRequest,
        getLearningPreferences(signal),
        getOperationalStatus(signal),
      ]);
      if (requestId !== latestLoadRequest.current) return false;

      const results = [
        healthResult,
        filesResult,
        summaryResult,
        actionsResult,
        recoveriesResult,
        backupResult,
        preferencesResult,
        operationsResult,
      ];
      if (results.some(isAbortedResult)) {
        return false;
      }

      if (healthResult.status === "fulfilled") {
        setService({ kind: "online", health: healthResult.value });
      } else {
        const message =
          healthResult.reason instanceof Error
            ? healthResult.reason.message
            : "Unknown error";
        setService({ kind: "offline", message });
      }
      if (filesResult.status === "fulfilled") {
        setFiles(filesResult.value);
        setFilesUnavailable(false);
      } else {
        setFilesUnavailable(true);
      }
      if (summaryResult.status === "fulfilled") setSummary(summaryResult.value);
      if (actionsResult.status === "fulfilled") setActions(actionsResult.value);
      if (recoveriesResult.status === "fulfilled") {
        setRecoveries(recoveriesResult.value);
      }
      if (
        backupResult.status === "fulfilled" &&
        backupResult.value !== null
      ) {
        setBackups(backupResult.value);
      }
      if (preferencesResult.status === "fulfilled") {
        setPreferences(preferencesResult.value);
      }
      if (operationsResult.status === "fulfilled") {
        setOperations(
          isOperationalStatus(operationsResult.value)
            ? operationsResult.value
            : null,
        );
      }

      const errors = [
        resultError("Intake files", filesResult),
        resultError("Intake summary", summaryResult),
        resultError("Action history", actionsResult),
        resultError("Recovery assessments", recoveriesResult),
        resultError("Backup history", backupResult),
        resultError("Learning preferences", preferencesResult),
        resultError("Operational status", operationsResult),
      ].filter((message): message is string => message !== null);
      setIntakeError(errors.length > 0 ? errors.join(" ") : null);

      return backupResult.status === "fulfilled";
    } catch (error: unknown) {
      if (requestId !== latestLoadRequest.current) return false;
      if (error instanceof DOMException && error.name === "AbortError") {
        return false;
      }
      setIntakeError(error instanceof Error ? error.message : "Unable to load intake");
      return false;
    }
  }, [filters]);

  useEffect(() => {
    const controller = new AbortController();
    let stopped = false;
    let refreshTimer: number | undefined;
    let lastBackupRefreshAt = Number.NEGATIVE_INFINITY;

    async function refreshIntake() {
      if (document.visibilityState !== "hidden") {
        const now = Date.now();
        const includeBackups =
          now - lastBackupRefreshAt >= BACKUP_REFRESH_INTERVAL_MS;
        const loaded = await loadIntake(controller.signal, includeBackups);
        if (includeBackups && loaded) lastBackupRefreshAt = Date.now();
      }
      if (!stopped) {
        refreshTimer = window.setTimeout(() => void refreshIntake(), 5_000);
      }
    }

    refreshTimer = window.setTimeout(() => void refreshIntake(), 200);
    return () => {
      stopped = true;
      controller.abort();
      if (refreshTimer !== undefined) window.clearTimeout(refreshTimer);
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

  async function handleReview(
    fileId: string,
    review: ApprovalRequest,
  ): Promise<boolean> {
    setReviewingFileId(fileId);
    try {
      await reviewRecommendation(fileId, review);
      await loadIntake();
      return true;
    } catch (error: unknown) {
      setIntakeError(error instanceof Error ? error.message : "Review failed");
      return false;
    } finally {
      setReviewingFileId(null);
    }
  }

  async function handleExecute(fileId: string) {
    if (
      !window.confirm(
        "Move this approved file into Nova’s library? Existing files will never be overwritten.",
      )
    ) {
      return;
    }
    setActingId(fileId);
    try {
      await executeApproved(fileId);
      await loadIntake();
    } catch (error: unknown) {
      setIntakeError(error instanceof Error ? error.message : "Execution failed");
    } finally {
      setActingId(null);
    }
  }

  async function handleUndo(operationId: string) {
    if (
      !window.confirm(
        "Restore this file to its original intake path? Nova will stop if that path is occupied.",
      )
    ) {
      return;
    }
    setActingId(operationId);
    try {
      await undoAction(operationId);
      await loadIntake();
    } catch (error: unknown) {
      setIntakeError(error instanceof Error ? error.message : "Undo failed");
    } finally {
      setActingId(null);
    }
  }

  async function handleBackup() {
    setIsBackingUp(true);
    setBackupNotice(null);
    try {
      await createDatabaseBackup();
      await loadIntake();
      setBackupNotice("Verified database backup created.");
    } catch (error: unknown) {
      setIntakeError(error instanceof Error ? error.message : "Backup failed");
    } finally {
      setIsBackingUp(false);
    }
  }

  async function handleRestore(backup: BackupRecord) {
    const requiredConfirmation = `RESTORE ${backup.filename}`;
    const confirmation = window.prompt(
      [
        "Restore this database backup?",
        "Nova will first create a safety snapshot of the current database.",
        "Document files are not changed.",
        `Type exactly: ${requiredConfirmation}`,
      ].join("\n\n"),
    );
    if (confirmation === null) return;
    if (confirmation !== requiredConfirmation) {
      setIntakeError("Restore cancelled because the confirmation did not match.");
      return;
    }

    setRestoringFilename(backup.filename);
    setBackupNotice(null);
    try {
      const result = await restoreDatabaseBackup(
        backup.filename,
        confirmation,
      );
      await loadIntake();
      setBackupNotice(
        `Restored ${result.restored_from}. Safety snapshot: ${result.safety_backup.filename}.`,
      );
    } catch (error: unknown) {
      setIntakeError(error instanceof Error ? error.message : "Restore failed");
    } finally {
      setRestoringFilename(null);
    }
  }

  async function handleLearningReset(preference: LearningPreferenceRecord) {
    const requiredConfirmation =
      `FORGET ${preference.document_type} / ${preference.base_category}`;
    const confirmation = window.prompt(
      [
        "Forget this learned filing preference?",
        `Nova will remove ${preference.stored_examples} stored example${
          preference.stored_examples === 1 ? "" : "s"
        }.`,
        "Document files and file-action history are not changed.",
        `Type exactly: ${requiredConfirmation}`,
      ].join("\n\n"),
    );
    if (confirmation === null) return;
    if (confirmation !== requiredConfirmation) {
      setIntakeError(
        "Learning reset cancelled because the confirmation did not match.",
      );
      return;
    }

    const preferenceKey =
      `${preference.document_type}\u0000${preference.base_category}`;
    setResettingPreference(preferenceKey);
    setLearningNotice(null);
    try {
      const result = await resetLearningPreference(
        preference.document_type,
        preference.base_category,
        confirmation,
      );
      await loadIntake();
      setLearningNotice(
        `Forgot ${result.removed_examples} stored learning example${
          result.removed_examples === 1 ? "" : "s"
        }.`,
      );
    } catch (error: unknown) {
      setIntakeError(
        error instanceof Error ? error.message : "Learning reset failed",
      );
    } finally {
      setResettingPreference(null);
    }
  }

  return (
    <AppShell
      activeWorkspace="intake"
      contentClassName="shell"
      status={(
        <div className="nav-status app-shell-service-status">
          <Status state={service} />
          <span className="phase">
            {service.kind === "online"
              ? `Intake MVP · ${service.health.version}`
              : "Intake MVP"}
          </span>
        </div>
      )}
    >

      <section className="hero">
        <div>
          <p className="eyebrow">
            Observe + understand + recommend + approve + execute · User controlled
          </p>
          <h1>Turn incoming files into useful context.</h1>
          <p className="lede">
            Add a document or image to <code>data/intake</code>. Nova reads it
            locally and prepares a recommendation. Nothing moves until you
            approve it.
          </p>
          <details className="hero-details">
            <summary>How Intake protects your files</summary>
            <p>
              Nova uses bounded local OCR when needed, records what it
              understands, and applies deterministic filing rules only when the
              evidence is strong enough. Review remains separate from execution.
              Only the explicit Move file action can place an approved item in
              Nova’s library.
            </p>
          </details>
        </div>
        <div className="safety-card">
          <span className="safety-icon" aria-hidden="true">✓</span>
          <div>
            <strong>No overwrite, verified undo</strong>
            <p>Nova checks the file hash and both paths before every move.</p>
          </div>
        </div>
      </section>

      <section
        className="workspace"
        aria-labelledby="intake-title"
        aria-busy={isScanning}
      >
        <div className="workspace-heading">
          <div>
            <p className="section-number">02–04 · Understand + review</p>
            <h2 id="intake-title">Review Nova’s recommendations</h2>
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

        {operations ? <OperationalHealth operations={operations} /> : null}

        <SearchControls filters={filters} onChange={setFilters} resultCount={files.length} />

        {intakeError ? (
          <p className="error-banner" role="alert">
            {intakeError}
          </p>
        ) : null}

        <div className="file-panel">
          {files.length === 0 && !filesUnavailable ? (
            <div className="empty-state">
              <span aria-hidden="true">↓</span>
              <h3>Your intake is empty</h3>
              <p>
                Drop a TXT, Markdown, PDF, DOCX, PNG, JPG, JPEG, TIFF, or BMP
                file into <code>data/intake</code>.
              </p>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <caption className="sr-only">
                  Nova intake files and processing status
                </caption>
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
                        <RecommendationView
                          fileId={file.id}
                          recommendation={file.recommendation}
                          approval={file.approval}
                          isBusy={
                            reviewingFileId === file.id || actingId === file.id
                          }
                          onReview={handleReview}
                          onExecute={handleExecute}
                        />
                      </td>
                      <td>{formatObserved(file.observed_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
        <LearningPanel
          preferences={preferences}
          resettingPreference={resettingPreference}
          notice={learningNotice}
          onReset={handleLearningReset}
        />
        <ActionHistory
          actions={actions}
          actingId={actingId}
          onUndo={handleUndo}
        />
        <RecoveryPanel assessments={recoveries} />
        <BackupPanel
          backups={backups}
          isBackingUp={isBackingUp}
          restoringFilename={restoringFilename}
          notice={backupNotice}
          onBackup={handleBackup}
          onRestore={handleRestore}
        />
      </section>
    </AppShell>
  );
}

function RecommendationView({
  fileId,
  recommendation,
  approval,
  isBusy,
  onReview,
  onExecute,
}: {
  fileId: string;
  recommendation: RecommendationRecord | null;
  approval: ApprovalRecord | null;
  isBusy: boolean;
  onReview: (fileId: string, review: ApprovalRequest) => Promise<boolean>;
  onExecute: (fileId: string) => Promise<void>;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [category, setCategory] = useState("");
  const [suggestedFilename, setSuggestedFilename] = useState("");
  const [destination, setDestination] = useState("");

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
  const effectiveCategory = approval?.category ?? recommendation.category ?? "";
  const effectiveFilename =
    approval?.suggested_filename ?? recommendation.suggested_filename ?? "";
  const effectiveDestination =
    approval?.destination ?? recommendation.destination ?? "";
  const approvalStatus = approval?.status ?? "pending";

  function beginEditing() {
    setCategory(effectiveCategory);
    setSuggestedFilename(effectiveFilename);
    setDestination(effectiveDestination);
    setIsEditing(true);
  }

  async function saveEdits(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const saved = await onReview(fileId, {
      action: "edit",
      category,
      suggested_filename: suggestedFilename,
      destination,
    });
    if (saved) setIsEditing(false);
  }

  if (isEditing) {
    return (
      <form className="recommendation-form" onSubmit={saveEdits}>
        <label>
          <span>Category</span>
          <input
            aria-label="Recommendation category"
            value={category}
            maxLength={80}
            required
            onChange={(event) => setCategory(event.target.value)}
          />
        </label>
        <label>
          <span>Suggested filename</span>
          <input
            aria-label="Suggested filename"
            value={suggestedFilename}
            maxLength={255}
            required
            onChange={(event) => setSuggestedFilename(event.target.value)}
          />
        </label>
        <label>
          <span>Destination</span>
          <input
            aria-label="Recommendation destination"
            value={destination}
            maxLength={500}
            required
            onChange={(event) => setDestination(event.target.value)}
          />
        </label>
        <div className="review-actions">
          <button type="submit" disabled={isBusy}>Save edits</button>
          <button
            type="button"
            className="secondary-button"
            disabled={isBusy}
            onClick={() => setIsEditing(false)}
          >
            Cancel
          </button>
        </div>
      </form>
    );
  }

  return (
    <>
      <span className={`badge approval ${approvalStatus}`}>
        {approvalLabel(approvalStatus)}
      </span>
      <span>
        {effectiveCategory} · {Math.round(recommendation.confidence * 100)}%
      </span>
      <strong>{effectiveFilename}</strong>
      <span>Destination: {effectiveDestination}</span>
      <span title={recommendation.reasons.join(" ")}>
        {recommendation.reasons[0]}
      </span>
      <span className="no-execution">
        {approvalStatus === "approved"
          ? "Approved. Moving still requires the separate action below."
          : "No file action will run until approval and explicit execution."}
      </span>
      {approvalStatus === "pending" ? (
        <div className="review-actions">
          <button
            type="button"
            disabled={isBusy}
            onClick={() => void onReview(fileId, { action: "approve" })}
          >
            Approve
          </button>
          <button
            type="button"
            className="secondary-button"
            disabled={isBusy}
            onClick={beginEditing}
          >
            Edit
          </button>
          <button
            type="button"
            className="secondary-button"
            disabled={isBusy}
            onClick={() => void onReview(fileId, { action: "reject" })}
          >
            Reject
          </button>
          <button
            type="button"
            className="secondary-button"
            disabled={isBusy}
            onClick={() => void onReview(fileId, { action: "ignore" })}
          >
            Ignore
          </button>
        </div>
      ) : (
        <div className="review-actions">
          {approvalStatus === "approved" ? (
            <button
              type="button"
              disabled={isBusy}
              onClick={() => void onExecute(fileId)}
            >
              Move file
            </button>
          ) : null}
          <button
            type="button"
            className="secondary-button"
            disabled={isBusy}
            onClick={() =>
              void onReview(fileId, {
                action: "edit",
                category: effectiveCategory,
                suggested_filename: effectiveFilename,
                destination: effectiveDestination,
              })
            }
          >
            Review again
          </button>
        </div>
      )}
    </>
  );
}

function LearningPanel({
  preferences,
  resettingPreference,
  notice,
  onReset,
}: {
  preferences: LearningPreferenceRecord[];
  resettingPreference: string | null;
  notice: string | null;
  onReset: (preference: LearningPreferenceRecord) => Promise<void>;
}) {
  return (
    <section className="learning-panel" aria-labelledby="learning-title">
      <div className="history-heading">
        <div>
          <p className="section-number">07 · Learn</p>
          <h3 id="learning-title">Learned filing preferences</h3>
        </div>
        <span>
          {preferences.length} group{preferences.length === 1 ? "" : "s"}
        </span>
      </div>
      <p className="learning-guidance">
        Nova learns destinations only from successful approved moves. Learning
        never approves or moves a file, and you can forget every stored example
        for a group here.
      </p>
      {notice ? (
        <p className="backup-notice" role="status">
          {notice}
        </p>
      ) : null}
      {preferences.length === 0 ? (
        <p className="history-empty">
          No filing preferences stored yet. Nova needs at least three consistent
          successful moves before changing a future destination suggestion.
        </p>
      ) : (
        <ul className="learning-list">
          {preferences.map((preference) => {
            const preferenceKey =
              `${preference.document_type}\u0000${preference.base_category}`;
            return (
              <li key={preferenceKey}>
                <div>
                  <span
                    className={`badge learning ${
                      preference.eligible ? "eligible" : "gathering"
                    }`}
                  >
                    {preference.eligible ? "Active suggestion" : "Gathering evidence"}
                  </span>
                  <strong>
                    {preference.document_type} · {preference.base_category}
                  </strong>
                  <span>
                    {preference.candidate_destination ??
                      "No single destination currently leads"}
                  </span>
                  <small>
                    {preference.supporting_examples} supporting ·{" "}
                    {preference.active_examples} active ·{" "}
                    {preference.stored_examples} stored
                  </small>
                </div>
                <button
                  type="button"
                  className="forget-button"
                  disabled={resettingPreference !== null}
                  onClick={() => void onReset(preference)}
                >
                  {resettingPreference === preferenceKey
                    ? "Forgetting…"
                    : "Forget examples"}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

function ActionHistory({
  actions,
  actingId,
  onUndo,
}: {
  actions: ActionRecord[];
  actingId: string | null;
  onUndo: (operationId: string) => Promise<void>;
}) {
  return (
    <section className="action-history" aria-labelledby="action-history-title">
      <div className="history-heading">
        <div>
          <p className="section-number">05–06 · Execute + audit</p>
          <h3 id="action-history-title">File action history</h3>
        </div>
        <span>{actions.length} operation{actions.length === 1 ? "" : "s"}</span>
      </div>
      {actions.length === 0 ? (
        <p className="history-empty">
          No file actions yet. Approvals alone never move a file.
        </p>
      ) : (
        <ul className="action-list">
          {actions.map((action) => (
            <li key={action.operation_id}>
              <div>
                <span className={`badge action ${action.status}`}>
                  {action.kind === "undo" ? "Undo" : "Move"} · {action.status}
                </span>
                <strong>
                  {action.source_path} → {action.destination_path}
                </strong>
                <span>{action.detail}</span>
                <small>{formatObserved(action.created_at)}</small>
              </div>
              {action.can_undo ? (
                <button
                  type="button"
                  className="secondary-button"
                  disabled={actingId === action.operation_id}
                  onClick={() => void onUndo(action.operation_id)}
                >
                  Undo move
                </button>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function RecoveryPanel({
  assessments,
}: {
  assessments: RecoveryAssessment[];
}) {
  return (
    <section
      className={`recovery-panel ${assessments.length > 0 ? "attention" : ""}`}
      aria-labelledby="recovery-title"
    >
      <div className="history-heading">
        <div>
          <p className="section-number">Operational safety</p>
          <h3 id="recovery-title">Interrupted operation check</h3>
        </div>
        <span>
          {assessments.length === 0
            ? "No incomplete operations"
            : `${assessments.length} need${assessments.length === 1 ? "s" : ""} review`}
        </span>
      </div>
      {assessments.length === 0 ? (
        <p className="history-empty">
          Nova found no operation left unfinished after the safety delay.
        </p>
      ) : (
        <>
          <p className="recovery-warning">
            Nova has not changed these files. Review both paths before retrying
            or manually reconciling an operation.
          </p>
          <ul className="recovery-list">
            {assessments.map((assessment) => (
              <li key={assessment.operation_id}>
                <span className={`badge recovery ${assessment.state}`}>
                  {recoveryLabel(assessment.state)}
                </span>
                <strong>
                  {assessment.source_path} → {assessment.destination_path}
                </strong>
                <span>{assessment.detail}</span>
                <small>
                  {assessment.kind === "undo" ? "Undo" : "Move"} started{" "}
                  {formatObserved(assessment.started_at)}
                </small>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

function recoveryLabel(state: RecoveryState): string {
  switch (state) {
    case "ready_to_retry":
      return "Source safe";
    case "completed_without_audit":
      return "Likely completed";
    case "copy_incomplete":
      return "Two verified copies";
    case "missing":
      return "Files missing";
    case "unsafe_path":
      return "Unsafe path";
    case "unreadable":
      return "Cannot inspect";
    default:
      return "Conflict";
  }
}

function BackupPanel({
  backups,
  isBackingUp,
  restoringFilename,
  notice,
  onBackup,
  onRestore,
}: {
  backups: BackupRecord[];
  isBackingUp: boolean;
  restoringFilename: string | null;
  notice: string | null;
  onBackup: () => Promise<void>;
  onRestore: (backup: BackupRecord) => Promise<void>;
}) {
  const [showAllBackups, setShowAllBackups] = useState(false);
  const visibleBackups = showAllBackups ? backups : backups.slice(0, 5);
  const backupTotalBytes = backups.reduce(
    (total, backup) => total + backup.size_bytes,
    0,
  );
  const checksumRecordedCount = backups.filter(
    (backup) => backup.checksum_recorded,
  ).length;
  const missingChecksumCount = backups.length - checksumRecordedCount;

  return (
    <section className="backup-panel" aria-labelledby="backup-title">
      <div className="history-heading">
        <div>
          <p className="section-number">Local resilience</p>
          <h3 id="backup-title">Database backups</h3>
        </div>
        <button
          type="button"
          disabled={isBackingUp}
          onClick={() => void onBackup()}
        >
          {isBackingUp ? "Creating backup…" : "Create backup"}
        </button>
      </div>
      <details className="backup-guidance">
        <summary>How backups protect your data</summary>
        <p>
          Nova creates a verified SQLite snapshot in <code>data/backups</code>.
          Backups can contain extracted document text, so keep them private.
          Download and Checksum both recheck the backup before saving a copy.
          Keep both files together on a different drive for recovery. Restore
          changes Nova&apos;s database history and index only; it never restores,
          removes, or overwrites document files. Nova creates a safety snapshot
          before every restore.
        </p>
      </details>
      {notice ? (
        <p className="backup-notice" role="status">
          {notice}
        </p>
      ) : null}
      {backups.length > 0 ? (
        <p className="backup-summary">
          <strong>
            {backups.length} backup{backups.length === 1 ? "" : "s"} retained
          </strong>
          <span>{formatBytes(backupTotalBytes)} total</span>
          <span>{checksumRecordedCount} checksums recorded</span>
          {missingChecksumCount > 0 ? (
            <span>{missingChecksumCount} need attention</span>
          ) : null}
        </p>
      ) : null}
      {backups.length === 0 ? (
        <p className="history-empty">No database backups have been created yet.</p>
      ) : (
        <>
          <ul className="backup-list" id="backup-history-list">
            {visibleBackups.map((backup) => (
              <li key={backup.filename}>
                <div>
                  <strong>{backup.filename}</strong>
                  <span>
                    {formatBytes(backup.size_bytes)} ·{" "}
                    {backup.checksum_recorded
                      ? "Checksum recorded"
                      : "Checksum unavailable"}{" "}
                    ·{" "}
                    {formatObserved(backup.created_at)}
                  </span>
                </div>
                <div className="backup-actions">
                  {backup.checksum_recorded ? (
                    <>
                      <a
                        href={backupDownloadUrl(backup.filename)}
                        download
                        aria-label={`Download integrity-checked copy of ${backup.filename}`}
                      >
                        Download
                      </a>
                      <a
                        href={backupChecksumDownloadUrl(backup.filename)}
                        download
                        aria-label={`Download checksum for ${backup.filename}`}
                      >
                        Checksum
                      </a>
                      <button
                        type="button"
                        className="restore-button"
                        aria-label={`Restore ${backup.filename}`}
                        disabled={restoringFilename !== null || isBackingUp}
                        onClick={() => void onRestore(backup)}
                      >
                        {restoringFilename === backup.filename
                          ? "Restoring…"
                          : "Restore"}
                      </button>
                    </>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
          {backups.length > 5 ? (
            <button
              type="button"
              className="backup-history-toggle"
              aria-controls="backup-history-list"
              aria-expanded={showAllBackups}
              onClick={() => setShowAllBackups((current) => !current)}
            >
              {showAllBackups
                ? "Show latest 5"
                : `Show all ${backups.length} backups`}
            </button>
          ) : null}
        </>
      )}
    </section>
  );
}

function approvalLabel(status: ApprovalRecord["status"] | "pending"): string {
  switch (status) {
    case "approved":
      return "Approved";
    case "rejected":
      return "Rejected";
    case "ignored":
      return "Ignored";
    default:
      return "Awaiting review";
  }
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
          placeholder='Words must all match; use quotes for a phrase'
          onChange={(event) => onChange({ ...filters, query: event.target.value })}
        />
      </label>
      <p className="search-help">
        Filename and title matches rank above content and evidence matches.
      </p>
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
        <label>
          <span>Review status</span>
          <select
            value={filters.approvalStatus ?? ""}
            onChange={(event) =>
              onChange({
                ...filters,
                approvalStatus:
                  event.target.value as IntakeFilters["approvalStatus"],
              })
            }
          >
            <option value="">All</option>
            <option value="pending">Awaiting review</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="ignored">Ignored</option>
          </select>
        </label>
        <div className="search-summary" aria-live="polite">
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
    return <p className="status pending" role="status"><span />Checking API</p>;
  }
  if (state.kind === "offline") {
    return <p className="status offline" role="status" title={state.message}><span />API unavailable</p>;
  }
  return <p className="status online" role="status"><span />Nova online</p>;
}

function OperationalHealth({
  operations,
}: {
  operations: OperationalStatus;
}) {
  const scanDetail =
    operations.last_scan_status === "never"
      ? "Waiting for first scan"
      : operations.last_scan_status === "failed"
        ? "Latest scan failed"
        : operations.last_scan_duration_ms === null
          ? "Latest scan completed"
          : `Latest scan ${formatDuration(operations.last_scan_duration_ms)}`;
  const storageDetail =
    operations.storage_free_bytes === null
      ? "Storage unavailable"
      : `${formatBytes(operations.storage_free_bytes)} free${
          operations.storage_free_percent === null
            ? ""
            : ` (${operations.storage_free_percent.toFixed(1)}%)`
        }`;

  return (
    <section
      className={`operations-panel ${operations.status}`}
      aria-label="System health"
    >
      <div>
        <span className="operations-label">System health</span>
        <strong>
          {operations.status === "healthy" ? "Healthy" : "Needs attention"}
        </strong>
      </div>
      <dl>
        <div>
          <dt>Local storage</dt>
          <dd>{storageDetail}</dd>
        </div>
        <div>
          <dt>Database</dt>
          <dd>
            {operations.database_size_bytes === null
              ? "Unavailable"
              : formatBytes(operations.database_size_bytes)}
          </dd>
        </div>
        <div>
          <dt>Intake monitor</dt>
          <dd>{scanDetail}</dd>
        </div>
      </dl>
      {operations.warnings.length > 0 ? (
        <ul>
          {operations.warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}

function isOperationalStatus(value: unknown): value is OperationalStatus {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Partial<OperationalStatus>;
  return (
    (candidate.status === "healthy" || candidate.status === "attention")
    && Array.isArray(candidate.warnings)
    && (
      candidate.last_scan_status === "ok"
      || candidate.last_scan_status === "failed"
      || candidate.last_scan_status === "never"
    )
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1_024) return `${bytes} B`;
  if (bytes < 1_048_576) return `${(bytes / 1_024).toFixed(1)} KB`;
  if (bytes < 1_073_741_824) return `${(bytes / 1_048_576).toFixed(1)} MB`;
  if (bytes < 1_099_511_627_776) {
    return `${(bytes / 1_073_741_824).toFixed(1)} GB`;
  }
  return `${(bytes / 1_099_511_627_776).toFixed(1)} TB`;
}

function formatDuration(milliseconds: number): string {
  if (milliseconds < 1_000) return `${milliseconds} ms`;
  return `${(milliseconds / 1_000).toFixed(1)} s`;
}

function formatObserved(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default App;
