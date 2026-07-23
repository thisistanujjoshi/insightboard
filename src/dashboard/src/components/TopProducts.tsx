import {
  Bar, BarChart, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import type { TopProduct } from "../api";
import { usePalette } from "../palette";

export default function TopProducts({ data }: { data: TopProduct[] }) {
  const p = usePalette();
  return (
    <section className="card">
      {/* Ranked magnitude: one hue; identity lives on the axis labels. */}
      <h2>Top products by revenue</h2>
      <ResponsiveContainer width="100%" height={Math.max(180, data.length * 44)}>
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 64, left: 8, bottom: 4 }}>
          <XAxis type="number" hide />
          <YAxis
            type="category"
            dataKey="name"
            width={210}
            tick={{ fill: p.textPrimary, fontSize: 13 }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            cursor={{ fill: "transparent" }}
            formatter={(value, key) =>
              key === "revenue" ? [`$${Number(value).toFixed(2)}`, "Revenue"] : [value, key]}
          />
          <Bar dataKey="revenue" fill={p.series} barSize={18} radius={[0, 4, 4, 0]}>
            <LabelList
              dataKey="revenue"
              position="right"
              formatter={(v) => {
                const n = Number(v);
                return `$${n >= 1000 ? `${(n / 1000).toFixed(1)}k` : n.toFixed(0)}`;
              }}
              style={{ fill: p.textSecondary, fontSize: 12 }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <details>
        <summary>View as table</summary>
        <table>
          <thead><tr><th>Product</th><th>SKU</th><th>Units</th><th>Revenue</th></tr></thead>
          <tbody>
            {data.map((t) => (
              <tr key={t.sku}>
                <td>{t.name}</td><td>{t.sku}</td><td>{t.units}</td>
                <td>${t.revenue.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </section>
  );
}
