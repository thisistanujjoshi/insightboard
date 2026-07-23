const BASE = import.meta.env.VITE_DATA_API ?? "http://localhost:8000";

export interface Summary { tenantId: string; revenue: number; orders: number }
export interface DailyRevenue { date: string; revenue: number }
export interface TopProduct { sku: string; name: string; units: number; revenue: number }
export interface ForecastPoint { date: string; revenue: number }
export interface Forecast {
  method: "moving_average" | "linear_regression";
  confidence: "low" | "medium" | "high";
  points: ForecastPoint[];
}
export interface Anomaly { date: string; revenue: number; expected: number; zScore: number }
export type FeedbackVariant = "sidebar" | "footer";
export type FeedbackRating = "up" | "down";
export interface FeedbackStats { [variant: string]: { up: number; down: number } }
export interface AskResult {
  sql: string;
  columns: string[];
  rows: Record<string, unknown>[];
  rowCount: number;
}
export interface AskErrorInfo { message: string; sql?: string }

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE}${path}`);
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  return response.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  return response.json() as Promise<T>;
}

export const fetchSummary = (tenant: string) =>
  get<Summary>(`/api/v1/tenants/${encodeURIComponent(tenant)}/summary`);
export const fetchRevenueDaily = (tenant: string) =>
  get<DailyRevenue[]>(`/api/v1/tenants/${encodeURIComponent(tenant)}/revenue-daily`);
export const fetchTopProducts = (tenant: string) =>
  get<TopProduct[]>(`/api/v1/tenants/${encodeURIComponent(tenant)}/top-products`);
export const fetchForecast = (tenant: string) =>
  get<Forecast>(`/api/v1/tenants/${encodeURIComponent(tenant)}/forecast`);
export const fetchAnomalies = (tenant: string) =>
  get<Anomaly[]>(`/api/v1/tenants/${encodeURIComponent(tenant)}/anomalies`);
export const submitFeedback = (
  tenant: string, variant: FeedbackVariant, rating: FeedbackRating, comment?: string,
) => post<{ id: number }>(`/api/v1/tenants/${encodeURIComponent(tenant)}/feedback`,
  { variant, rating, comment });

// The data service returns rejected/timed-out queries as
// `{ detail: { message, sql } }` so the UI can still show what SQL was
// attempted (per the PRD: "show the SQL for trust", even on failure).
export function parseAskError(body: unknown): AskErrorInfo {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return { message: detail };
  if (detail && typeof detail === "object") {
    const d = detail as { message?: unknown; sql?: unknown };
    return {
      message: typeof d.message === "string" ? d.message : "Request failed.",
      sql: typeof d.sql === "string" ? d.sql : undefined,
    };
  }
  return { message: "Request failed." };
}

export async function askQuestion(tenant: string, question: string): Promise<AskResult> {
  const response = await fetch(`${BASE}/api/v1/tenants/${encodeURIComponent(tenant)}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  const body = await response.json();
  if (!response.ok) {
    const { message, sql } = parseAskError(body);
    throw Object.assign(new Error(message), { sql });
  }
  return body as AskResult;
}
