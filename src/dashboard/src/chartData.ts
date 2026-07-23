import type { DailyRevenue, ForecastPoint } from "./api";

export interface RevenueRow { date: string; revenue?: number; forecastRevenue?: number }

/**
 * Merges actuals with a forecast projection into one row series for the chart.
 * The last actual point is duplicated onto `forecastRevenue` so the dashed
 * forecast line connects to the solid actual line with no visual gap.
 */
export function buildRevenueRows(data: DailyRevenue[], forecastPoints: ForecastPoint[]): RevenueRow[] {
  const rows: RevenueRow[] = data.map((d) => ({ date: d.date, revenue: d.revenue }));
  if (forecastPoints.length > 0 && rows.length > 0) {
    rows[rows.length - 1].forecastRevenue = rows[rows.length - 1].revenue;
    for (const point of forecastPoints) {
      rows.push({ date: point.date, forecastRevenue: point.revenue });
    }
  }
  return rows;
}
