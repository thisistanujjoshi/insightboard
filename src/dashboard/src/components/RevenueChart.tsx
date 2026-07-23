import {
  CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import type { DailyRevenue } from "../api";
import { usePalette } from "../palette";

export default function RevenueChart({ data }: { data: DailyRevenue[] }) {
  const p = usePalette();
  return (
    <section className="card">
      {/* Single series: the title names it — no legend needed. */}
      <h2>Daily revenue</h2>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data} margin={{ top: 8, right: 12, left: 4, bottom: 0 }}>
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
            formatter={(value) => [`$${Number(value).toFixed(2)}`, "Revenue"]}
            contentStyle={{ borderRadius: 8 }}
          />
          <Line
            type="monotone"
            dataKey="revenue"
            stroke={p.series}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
      <details>
        <summary>View as table</summary>
        <table>
          <thead><tr><th>Date</th><th>Revenue</th></tr></thead>
          <tbody>
            {data.map((d) => (
              <tr key={d.date}><td>{d.date}</td><td>${d.revenue.toFixed(2)}</td></tr>
            ))}
          </tbody>
        </table>
      </details>
    </section>
  );
}
