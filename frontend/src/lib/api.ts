const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface HealthResponse {
  status: "ok";
  service: string;
  version: string;
  environment: string;
  timestamp: string;
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

export interface IntakeFilters {
  query?: string;
  status?: IntakeFile["status"] | "";
  understandingStatus?: UnderstandingRecord["status"] | "";
  extension?: string;
  documentType?: string;
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
  const query = parameters.size ? `?${parameters.toString()}` : "";
  return request<IntakeFile[]>(`/api/v1/intake/files${query}`, { signal });
}

export async function getIntakeSummary(signal?: AbortSignal): Promise<IntakeSummary> {
  return request<IntakeSummary>("/api/v1/intake/summary", { signal });
}

export async function scanIntake(): Promise<IntakeScanResult> {
  return request<IntakeScanResult>("/api/v1/intake/scan", { method: "POST" });
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, init);
  if (!response.ok) {
    throw new Error(`Nova API returned ${response.status}`);
  }
  return response.json() as Promise<T>;
}
