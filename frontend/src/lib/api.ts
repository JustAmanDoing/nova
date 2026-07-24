const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface HealthResponse {
  status: "ok";
  service: string;
  version: string;
  environment: string;
  timestamp: string;
}

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${API_URL}/api/v1/health`, { signal });

  if (!response.ok) {
    throw new Error(`Nova API returned ${response.status}`);
  }

  return response.json() as Promise<HealthResponse>;
}

