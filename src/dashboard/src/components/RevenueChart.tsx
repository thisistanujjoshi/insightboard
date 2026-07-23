import {
  CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import type { Anomaly, DailyRevenue, Forecast } from "../api";
import { buildRevenueRows, type RevenueRow } from "../chartData";
import { usePalette } from "../palette";

interface Props {
  data: DailyRevenue[];
  forecast: Forecast | null;
  anomalies: Anomaly[];
}

const CONFIDENCE_LABEL: Record<Forecast["confidence"], string> = {
  low: "Low confidence (moving average — under 21 days of history)",
  medium: "Medium confidence (trend model)",
  high: "High confidence (trend model, 60+ days of history)",
};

export default function RevenueChart({ data, forecast, anomalies }: Props) {
  const p = usePalette();
  const anomalyDates = new Set(anomalies.map((a) => a.date));
  const rows = buildRevenueRows(data, forecast?.points ?? []);

  return (
    <section className="card">
      <div className="card-header">
        {/* Single measure across two line styles: title names it, a small
            key explains style/marker meaning (not a categorical legend). */}
        <h2>Daily revenue</h2>
        {forecast && forecast.points.length > 0 && (
          <span className="badge" title={CONFIDENCE_LABEL[forecast.confidence]}>
            {forecast.confidence} confidence forecast
          </span>
        )}
      </div>
      <div className="chart-key">
        <span><i className="key-line" /> Actual</span>
        <span><i className="key-line key-line--dashed" /> Forecast</span>
        {anomalies.length > 0 && <span><i className="key-dot" /> Anomaly</span>}
      </div>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={rows} margin={{ top: 8, right: 12, left: 4, bottom: 0 }}>
          <CartesianGrid stroke={p.grid} strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fill: p.textSecondary, fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: p.grid }}
            minTickGap={40}
          />
          <YAxis
            tick={{ fill: p.textSecondary, fontSize: 12 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: number) => `$${v >= 1000 ? `${(v / 1000).toFixed(1)}k` : v}`}
            width={52}
          />
          <Tooltip
            cursor={{ stroke: p.textSecondary, strokeWidth: 1 }}
            formatter={(value, key) => [
              `$${Number(value).toFixed(2)}`,
              key === "forecastRevenue" ? "Forecast" : "Revenue",
            ]}
            contentStyle={{ borderRadius: 8 }}
          />
          <Line
            type="monotone"
            dataKey="revenue"
            stroke={p.series}
            strokeWidth={2}
            dot={(dotProps) => {
              const { cx, cy, payload } = dotProps as { cx: number; cy: number; payload: RevenueRow };
              if (!anomalyDates.has(payload.date)) return <g key={`d-${payload.date}`} />;
              return (
                <circle
                  key={`a-${payload.date}`}
                  cx={cx} cy={cy} r={5}
                  fill={p.error} stroke={p.surface} strokeWidth={1.5}
                />
              );
            }}
            activeDot={{ r: 4 }}
            isAnimationActive={false}
          />
          {forecast && forecast.points.length > 0 && (
            <Line
              type="monotone"
              dataKey="forecastRevenue"
              stroke={p.series}
              strokeWidth={2}
              strokeDasharray="5 4"
              dot={false}
              isAnimationActive={false}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
      <details>
        <summary>View as table</summary>
        <table>
          <thead><tr><th>Date</th><th>Revenue</th><th>Note</th></tr></thead>
          <tbody>
            {data.map((d) => {
              const anomaly = anomalies.find((a) => a.date === d.date);
              return (
                <tr key={d.date}>
                  <td>{d.date}</td>
                  <td>${d.revenue.toFixed(2)}</td>
                  <td>{anomaly ? `Anomaly (expected ~$${anomaly.expected.toFixed(0)})` : ""}</td>
                </tr>
              );
            })}
            {forecast?.points.map((f) => (
              <tr key={f.date}>
                <td>{f.date}</td><td>${f.revenue.toFixed(2)} (forecast)</td><td></td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </section>
  );
}
