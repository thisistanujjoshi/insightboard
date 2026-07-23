import { describe, expect, it } from "vitest";
import { buildRevenueRows } from "./chartData";

const ACTUALS = [
  { date: "2026-01-01", revenue: 100 },
  { date: "2026-01-02", revenue: 150 },
];
const FORECAST_POINTS = [
  { date: "2026-01-03", revenue: 120 },
  { date: "2026-01-04", revenue: 130 },
];

describe("buildRevenueRows", () => {
  it("returns bare actuals when there is no forecast", () => {
    const rows = buildRevenueRows(ACTUALS, []);
    expect(rows).toEqual([
      { date: "2026-01-01", revenue: 100 },
      { date: "2026-01-02", revenue: 150 },
    ]);
  });

  it("duplicates the last actual onto forecastRevenue so the lines connect", () => {
    const rows = buildRevenueRows(ACTUALS, FORECAST_POINTS);
    expect(rows[1]).toEqual({ date: "2026-01-02", revenue: 150, forecastRevenue: 150 });
  });

  it("appends forecast-only rows after the actuals", () => {
    const rows = buildRevenueRows(ACTUALS, FORECAST_POINTS);
    expect(rows.slice(2)).toEqual([
      { date: "2026-01-03", forecastRevenue: 120 },
      { date: "2026-01-04", forecastRevenue: 130 },
    ]);
    expect(rows).toHaveLength(4);
  });

  it("does nothing with a forecast but no actual history", () => {
    expect(buildRevenueRows([], FORECAST_POINTS)).toEqual([]);
  });
});
