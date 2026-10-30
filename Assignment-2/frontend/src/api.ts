export interface ComponentMetadata {
  ready: boolean;
  version: string | null;
}

export interface ServiceMetadata {
  classifier: ComponentMetadata;
  summarizer: ComponentMetadata;
  knowledge_index: ComponentMetadata;
}

export interface AnalysisResponse {
  classification: Record<string, unknown> | string;
  summary: string;
}

export interface KnowledgeSource {
  id?: string;
  source_id?: string;
  title?: string;
  section?: string;
  excerpt?: string;
  text?: string;
  url?: string;
}

export interface ChatResponse {
  answer?: string;
  sources?: KnowledgeSource[];
}

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "/api").replace(/\/$/, "");

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`, init);
  } catch {
    throw new ApiError("The API is unavailable. Check that the backend is running.", 0);
  }

  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const detail =
      typeof payload === "object" &&
      payload !== null &&
      "detail" in payload &&
      typeof payload.detail === "string"
        ? payload.detail
        : `The request failed with status ${response.status}.`;
    throw new ApiError(detail, response.status);
  }

  return payload as T;
}

export function getServiceMetadata(signal?: AbortSignal): Promise<ServiceMetadata> {
  return requestJson<ServiceMetadata>("/metadata", { signal });
}

export function analyzeSupportMessage(message: string): Promise<AnalysisResponse> {
  return requestJson<AnalysisResponse>("/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
}

export function askKnowledgeQuestion(question: string): Promise<ChatResponse> {
  return requestJson<ChatResponse>("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
}