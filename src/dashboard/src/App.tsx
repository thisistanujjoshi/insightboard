import { useCallback, useEffect, useState } from "react";
import {
  fetchAnomalies, fetchForecast, fetchRevenueDaily, fetchSummary, fetchTopProducts,
  type Anomaly, type DailyRevenue, type Forecast, type Summary, type TopProduct,
} from "./api";
import RevenueChart from "./components/RevenueChart";
import TopProducts from "./components/TopProducts";
import FeedbackWidget from "./components/FeedbackWidget";
import AskBox from "./components/AskBox";

export default function App() {
  const [tenant, setTenant] = useState("demo");
  const [input, setInput] = useState("demo");
  const [summary, setSummary] = useState<Summary | null>(null);
  const [daily, setDaily] = useState<DailyRevenue[]>([]);
  const [top, setTop] = useState<TopProduct[]>([]);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (t: string) => {
    setError(null);
    try {
      const [s, d, p, f, a] = await Promise.all([
        fetchSummary(t), fetchRevenueDaily(t), fetchTopProducts(t),
        fetchForecast(t), fetchAnomalies(t),
      ]);
      setSummary(s); setDaily(d); setTop(p); setForecast(f); setAnomalies(a);
    } catch {
      setError("Data service unavailable — is it running on port 8000?");
    }
  }, []);

  useEffect(() => { void load(tenant); }, [tenant, load]);

  const avgOrder = summary && summary.orders > 0 ? summary.revenue / summary.orders : 0;

  return (
    <div className="layout">
      <header>
        <h1>Insight<span>Board</span></h1>
        <form onSubmit={(e) => { e.preventDefault(); setTenant(input.trim() || "demo"); }}>
          <label htmlFor="tenant">Tenant</label>
          <input id="tenant" value={input} onChange={(e) => setInput(e.target.value)} />
          <button type="submit">Load</button>
        </form>
      </header>

      {error && <p className="error">{error}</p>}

      {summary && !error && (
        <>
          <div className="tiles">
            <div className="tile">
              <span className="tile-label">Revenue (all time)</span>
              <span className="tile-value">
                ${summary.revenue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </span>
            </div>
            <div className="tile">
              <span className="tile-label">Orders</span>
              <span className="tile-value">{summary.orders.toLocaleString()}</span>
            </div>
            <div className="tile">
              <span className="tile-label">Avg order value</span>
              <span className="tile-value">${avgOrder.toFixed(2)}</span>
            </div>
          </div>

          {daily.length === 0 ? (
            <p className="empty">
              No data for tenant “{tenant}” yet — seed it with
              {" "}<code>python scripts/generate_demo.py {tenant}</code> in src/data-service.
            </p>
          ) : (
            <>
              <RevenueChart data={daily} forecast={forecast} anomalies={anomalies} />
              <TopProducts data={top} />
            </>
          )}

          <AskBox tenant={tenant} />
        </>
      )}

      <footer>InsightBoard — analytics for small shops. Data: FastAPI + PostgreSQL warehouse.</footer>

      {summary && !error && <FeedbackWidget tenant={tenant} />}
    </div>
  );
}
