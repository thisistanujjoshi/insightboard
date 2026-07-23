import { useState, type FormEvent } from "react";
import { askQuestion, type AskResult } from "../api";

export default function AskBox({ tenant }: { tenant: string }) {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AskResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [errorSql, setErrorSql] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(false);

  async function ask(e: FormEvent) {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) return;
    setLoading(true);
    setError(null);
    setErrorSql(undefined);
    try {
      setResult(await askQuestion(tenant, trimmed));
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setErrorSql((err as { sql?: string })?.sql);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="card ask-box">
      <h2>Ask in English</h2>
      <form className="ask-form" onSubmit={(e) => void ask(e)}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. what are the top products?"
          aria-label="Ask a question about this tenant's data"
        />
        <button type="submit" disabled={loading}>{loading ? "Asking…" : "Ask"}</button>
      </form>

      {error && (
        <div className="ask-error">
          <p className="error">{error}</p>
          {errorSql && (
            <details>
              <summary>View attempted SQL</summary>
              <pre>{errorSql}</pre>
            </details>
          )}
        </div>
      )}

      {result && (
        <>
          {result.rows.length === 0 ? (
            <p className="empty">No rows matched.</p>
          ) : (
            <table>
              <thead>
                <tr>{result.columns.map((c) => <th key={c}>{c}</th>)}</tr>
              </thead>
              <tbody>
                {result.rows.map((row, i) => (
                  <tr key={i}>
                    {result.columns.map((c) => <td key={c}>{String(row[c])}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <details>
            <summary>View SQL</summary>
            <pre>{result.sql}</pre>
          </details>
        </>
      )}
    </section>
  );
}
