const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const LOCAL_ACTION_HEADER = "X-Nova-Intent";
const LOCAL_ACTION_VALUE = "local-user-action";

export interface HealthResponse {
  status: "ok";
  service: string;
  version: string;
  environment: string;
  timestamp: string;
}

export interface ChatModel {
  name: string;
  size_bytes: number;
  parameter_size: string | null;
  quantization_level: string | null;
}

export interface ChatMessage {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  model: string | null;
  created_at: string;
  knowledge_checked: boolean;
  sources: ChatKnowledgeSource[];
}

export interface ChatKnowledgeSource {
  record_id: string;
  citation_label: string;
  title: string;
  kind: string;
  content: string;
  relative_path: string;
  sha256: string;
  score: number;
}

export interface ChatConversationSummary {
  id: string;
  title: string;
  model: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ChatConversation extends ChatConversationSummary {
  messages: ChatMessage[];
}

export type ChatStreamEvent =
  | { type: "user"; message: ChatMessage }
  | { type: "delta"; content: string }
  | { type: "done"; message: ChatMessage }
  | {
      type: "knowledge";
      checked: true;
      sources: ChatKnowledgeSource[];
    }
  | { type: "knowledge_warning"; message: string }
  | { type: "error"; message: string };

export type KnowledgeKind =
  | "fact"
  | "preference"
  | "goal"
  | "project"
  | "lesson"
  | "rule"
  | "reference";

export type KnowledgeCandidateStatus = "pending" | "approved" | "rejected";

export interface KnowledgeCandidate {
  id: string;
  conversation_id: string;
  source_message_id: string;
  kind: KnowledgeKind;
  title: string;
  content: string;
  source_excerpt: string;
  reason: string;
  confidence: number;
  explicit_request: boolean;
  status: KnowledgeCandidateStatus;
  created_at: string;
  reviewed_at: string | null;
  record_path: string | null;
  duplicate_record_id: string | null;
  duplicate_title: string | null;
  duplicate_path: string | null;
  duplicate_score: number | null;
}

export interface KnowledgeReviewRequest {
  action: "approve" | "reject";
  kind?: KnowledgeKind;
  title?: string;
  content?: string;
  duplicate_confirmation?: string;
}

export type KnowledgeRecordStatus = "active" | "retired";

export interface KnowledgeRecord {
  id: string;
  candidate_id: string;
  kind: KnowledgeKind;
  title: string;
  content: string;
  relative_path: string;
  sha256: string;
  created_at: string;
  status: KnowledgeRecordStatus;
  revision: number;
  updated_at: string;
  retired_at: string | null;
}

export type KnowledgeRecordLifecycleRequest =
  | {
      action: "update";
      kind: KnowledgeKind;
      title: string;
      content: string;
      duplicate_confirmation?: string;
    }
  | {
      action: "retire";
      confirmation: string;
    };

export interface KnowledgeSnapshot {
  filename: string;
  size_bytes: number;
  sha256: string;
  record_count: number;
  file_count: number;
  created_at: string;
}

export interface OperationalStatus {
  status: "healthy" | "attention";
  uptime_seconds: number;
  database_size_bytes: number | null;
  storage_free_bytes: number | null;
  storage_total_bytes: number | null;
  storage_free_percent: number | null;
  last_scan_status: "ok" | "failed" | "never";
  last_scan_completed_at: string | null;
  last_scan_duration_ms: number | null;
  warnings: string[];
}

export interface IntakeFile {
  id: string;
  relative_path: string;
  original_name: string;
  extension: string;
  size_bytes: number;
  modified_at: string;
  observed_at: string;
  sha256: string;
  status: "observed" | "duplicate";
  duplicate_of: string | null;
  understanding: UnderstandingRecord | null;
  recommendation: RecommendationRecord | null;
  approval: ApprovalRecord | null;
}

export interface UnderstandingRecord {
  status: "ready" | "empty" | "unsupported" | "too_large" | "failed";
  document_type: string | null;
  title: string | null;
  text_preview: string | null;
  word_count: number | null;
  character_count: number | null;
  evidence: string;
  error: string | null;
  error_code: string | null;
  extraction_method: string;
  retryable: boolean;
  understood_at: string;
}

export interface RecommendationRecord {
  outcome: "suggested" | "insufficient_evidence";
  category: string | null;
  suggested_filename: string | null;
  destination: string | null;
  confidence: number;
  reasons: string[];
  generated_at: string;
}

export type ApprovalStatus = "pending" | "approved" | "rejected" | "ignored";

export interface ApprovalRecord {
  status: ApprovalStatus;
  category: string;
  suggested_filename: string;
  destination: string;
  recommendation_generated_at: string;
  reviewed_at: string;
}

export interface ApprovalRequest {
  action: "edit" | "approve" | "reject" | "ignore";
  category?: string;
  suggested_filename?: string;
  destination?: string;
}

export interface ActionRecord {
  operation_id: string;
  file_id: string;
  kind: "move" | "undo";
  status: "started" | "succeeded" | "failed";
  source_path: string;
  destination_path: string;
  sha256: string;
  related_operation_id: string | null;
  detail: string;
  created_at: string;
  can_undo: boolean;
}

export type RecoveryState =
  | "ready_to_retry"
  | "completed_without_audit"
  | "copy_incomplete"
  | "conflict"
  | "missing"
  | "unsafe_path"
  | "unreadable";

export interface RecoveryAssessment {
  operation_id: string;
  kind: "move" | "undo";
  state: RecoveryState;
  source_path: string;
  destination_path: string;
  expected_sha256: string;
  source_sha256: string | null;
  destination_sha256: string | null;
  detail: string;
  started_at: string;
  assessed_at: string;
}

export interface BackupRecord {
  filename: string;
  size_bytes: number;
  sha256: string | null;
  created_at: string;
  checksum_recorded: boolean;
  verified: boolean;
}

export interface RestoreResult {
  restored_from: string;
  restored_from_sha256: string;
  safety_backup: BackupRecord;
  restored_at: string;
  detail: string;
}

export interface LearningPreferenceRecord {
  document_type: string;
  base_category: string;
  candidate_destination: string | null;
  supporting_examples: number;
  active_examples: number;
  stored_examples: number;
  preference_share: number;
  eligible: boolean;
  revision: number;
}

export interface LearningResetResult {
  document_type: string;
  base_category: string;
  removed_examples: number;
  reset_at: string;
  detail: string;
}

export interface IntakeFilters {
  query?: string;
  status?: IntakeFile["status"] | "";
  understandingStatus?: UnderstandingRecord["status"] | "";
  extension?: string;
  documentType?: string;
  approvalStatus?: ApprovalStatus | "";
}

export interface IntakeScanResult {
  scanned: number;
  added: number;
  updated: number;
  removed: number;
  duplicates: number;
}

export interface IntakeSummary {
  files_observed: number;
  understood: number;
  ready_for_review: number;
  exact_duplicates: number;
}

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return request<HealthResponse>("/api/v1/health", { signal });
}

export async function getOperationalStatus(
  signal?: AbortSignal,
): Promise<OperationalStatus> {
  return request<OperationalStatus>("/api/v1/system/status", { signal });
}

export async function getChatModels(
  signal?: AbortSignal,
): Promise<ChatModel[]> {
  return request<ChatModel[]>("/api/v1/chat/models", { signal });
}

export async function getChatConversations(
  signal?: AbortSignal,
): Promise<ChatConversationSummary[]> {
  return request<ChatConversationSummary[]>("/api/v1/chat/conversations", {
    signal,
  });
}

export async function createChatConversation(
  title = "New conversation",
): Promise<ChatConversationSummary> {
  return request<ChatConversationSummary>("/api/v1/chat/conversations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
}

export async function getChatConversation(
  conversationId: string,
  signal?: AbortSignal,
): Promise<ChatConversation> {
  return request<ChatConversation>(
    `/api/v1/chat/conversations/${encodeURIComponent(conversationId)}`,
    { signal },
  );
}

export async function streamChatMessage(
  conversationId: string,
  model: string,
  content: string,
  onEvent: (event: ChatStreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(
    `${API_URL}/api/v1/chat/conversations/${encodeURIComponent(conversationId)}/messages`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        [LOCAL_ACTION_HEADER]: LOCAL_ACTION_VALUE,
      },
      body: JSON.stringify({ model, content }),
      signal,
    },
  );
  if (!response.ok) {
    throw await responseError(response);
  }
  if (!response.body) {
    throw new Error("Nova API returned an empty chat stream.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (line.trim()) onEvent(JSON.parse(line) as ChatStreamEvent);
    }
    if (done) break;
  }
  if (buffer.trim()) onEvent(JSON.parse(buffer) as ChatStreamEvent);
}

export async function getKnowledgeCandidates(
  status?: KnowledgeCandidateStatus,
  signal?: AbortSignal,
): Promise<KnowledgeCandidate[]> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return request<KnowledgeCandidate[]>(`/api/v1/knowledge/candidates${query}`, {
    signal,
  });
}

export async function reviewKnowledgeCandidate(
  candidateId: string,
  review: KnowledgeReviewRequest,
): Promise<KnowledgeCandidate> {
  return request<KnowledgeCandidate>(
    `/api/v1/knowledge/candidates/${encodeURIComponent(candidateId)}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(review),
    },
  );
}

export async function getKnowledgeRecords(
  signal?: AbortSignal,
): Promise<KnowledgeRecord[]> {
  return request<KnowledgeRecord[]>("/api/v1/knowledge/records", { signal });
}

export async function updateKnowledgeRecord(
  recordId: string,
  lifecycle: KnowledgeRecordLifecycleRequest,
): Promise<KnowledgeRecord> {
  return request<KnowledgeRecord>(
    `/api/v1/knowledge/records/${encodeURIComponent(recordId)}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(lifecycle),
    },
  );
}

export async function createKnowledgeSnapshot(): Promise<KnowledgeSnapshot> {
  return request<KnowledgeSnapshot>("/api/v1/knowledge/snapshots", {
    method: "POST",
  });
}

export async function getBackups(
  signal?: AbortSignal,
): Promise<BackupRecord[]> {
  return request<BackupRecord[]>("/api/v1/backups", { signal });
}

export async function createDatabaseBackup(): Promise<BackupRecord> {
  return request<BackupRecord>("/api/v1/backups", { method: "POST" });
}

export async function restoreDatabaseBackup(
  filename: string,
  confirmation: string,
): Promise<RestoreResult> {
  return request<RestoreResult>(
    `/api/v1/backups/${encodeURIComponent(filename)}/restore`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ confirmation }),
    },
  );
}

export async function getLearningPreferences(
  signal?: AbortSignal,
): Promise<LearningPreferenceRecord[]> {
  return request<LearningPreferenceRecord[]>("/api/v1/intake/preferences", {
    signal,
  });
}

export async function resetLearningPreference(
  documentType: string,
  baseCategory: string,
  confirmation: string,
): Promise<LearningResetResult> {
  return request<LearningResetResult>("/api/v1/intake/preferences/reset", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      document_type: documentType,
      base_category: baseCategory,
      confirmation,
    }),
  });
}

export function backupDownloadUrl(filename: string): string {
  return `${API_URL}/api/v1/backups/${encodeURIComponent(filename)}`;
}

export function backupChecksumDownloadUrl(filename: string): string {
  return `${backupDownloadUrl(filename)}/checksum`;
}

export async function getIntakeFiles(
  filters: IntakeFilters = {},
  signal?: AbortSignal,
): Promise<IntakeFile[]> {
  const parameters = new URLSearchParams();
  if (filters.query?.trim()) parameters.set("q", filters.query.trim());
  if (filters.status) parameters.set("status", filters.status);
  if (filters.understandingStatus) {
    parameters.set("understanding_status", filters.understandingStatus);
  }
  if (filters.extension?.trim()) parameters.set("extension", filters.extension.trim());
  if (filters.documentType?.trim()) {
    parameters.set("document_type", filters.documentType.trim());
  }
  if (filters.approvalStatus) {
    parameters.set("approval_status", filters.approvalStatus);
  }
  const query = parameters.size ? `?${parameters.toString()}` : "";
  return request<IntakeFile[]>(`/api/v1/intake/files${query}`, { signal });
}

export async function getIntakeSummary(signal?: AbortSignal): Promise<IntakeSummary> {
  return request<IntakeSummary>("/api/v1/intake/summary", { signal });
}

export async function scanIntake(): Promise<IntakeScanResult> {
  return request<IntakeScanResult>("/api/v1/intake/scan", { method: "POST" });
}

export async function reviewRecommendation(
  fileId: string,
  review: ApprovalRequest,
): Promise<ApprovalRecord> {
  return request<ApprovalRecord>(`/api/v1/intake/files/${fileId}/approval`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(review),
  });
}

export async function getActionHistory(
  signal?: AbortSignal,
): Promise<ActionRecord[]> {
  return request<ActionRecord[]>("/api/v1/intake/actions", { signal });
}

export async function getRecoveryAssessments(
  signal?: AbortSignal,
): Promise<RecoveryAssessment[]> {
  return request<RecoveryAssessment[]>("/api/v1/intake/actions/recovery", {
    signal,
  });
}

export async function executeApproved(fileId: string): Promise<ActionRecord> {
  return request<ActionRecord>(`/api/v1/intake/files/${fileId}/execute`, {
    method: "POST",
  });
}

export async function undoAction(operationId: string): Promise<ActionRecord> {
  return request<ActionRecord>(`/api/v1/intake/actions/${operationId}/undo`, {
    method: "POST",
  });
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const method = init?.method?.toUpperCase() ?? "GET";
  const headers = new Headers(init?.headers);
  if (method !== "GET" && method !== "HEAD") {
    headers.set(LOCAL_ACTION_HEADER, LOCAL_ACTION_VALUE);
  }
  const response = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (!response.ok) {
    throw await responseError(response);
  }
  return response.json() as Promise<T>;
}

async function responseError(response: Response): Promise<Error> {
  let detail = "";
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") detail = `: ${body.detail}`;
  } catch {
    // The status is still useful when the response is not JSON.
  }
  return new Error(`Nova API returned ${response.status}${detail}`);
}
