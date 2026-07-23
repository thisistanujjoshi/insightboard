const BASE = import.meta.env.VITE_DATA_API ?? "http://localhost:8000";

export interface Summary { tenantId: string; revenue: number; orders: number }
export interface DailyRevenue { date: string; revenue: number }
export interface TopProduct { sku: string; name: string; units: number; revenue: number }

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE}${path}`);
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  return response.json() as Promise<T>;
}

export const fetchSummary = (tenant: string) =>
  get<Summary>(`/api/v1/tenants/${encodeURIComponent(tenant)}/summary`);
export const fetchRevenueDaily = (tenant: string) =>
  get<DailyRevenue[]>(`/api/v1/tenants/${encodeURIComponent(tenant)}/revenue-daily`);
export const fetchTopProducts = (tenant: string) =>
  get<TopProduct[]>(`/api/v1/tenants/${encodeURIComponent(tenant)}/top-products`);
