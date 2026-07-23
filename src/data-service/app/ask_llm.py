"""Translates a plain-English question into SQL.

The model is only ever told about one view, `orders`, and is never shown a
tenant identifier — see nlsql.py for how that view gets built and enforced.
Same pluggable-client pattern as NexusCommerce's AiSupport: a real Anthropic
client for prod/demo, a deterministic stub for offline dev and CI.
"""

from typing import Protocol

SCHEMA_PROMPT = """\
You translate an analyst's question into a single read-only SQL query.

You have access to exactly one view named `orders` with these columns:
  order_id      TEXT
  placed_at     TIMESTAMP
  product_sku   TEXT
  product_name  TEXT
  quantity      INTEGER
  unit_price    NUMERIC
  line_total    NUMERIC   -- quantity * unit_price, precomputed

Rules:
- Output ONLY the SQL statement. No markdown fences, no explanation, no semicolon.
- Query only the `orders` view. Never reference any other table.
- There is no tenant or customer identifier column visible to you — never
  invent one or filter on one.
- Prefer aggregate queries (SUM, COUNT, AVG, GROUP BY) when the question
  asks about totals, trends, or comparisons.
"""


class AskLlm(Protocol):
    async def generate_sql(self, question: str) -> str: ...


class AnthropicAskLlm:
    def __init__(self, model: str) -> None:
        try:
            import truststore
            truststore.inject_into_ssl()
        except ImportError:
            pass
        from anthropic import AsyncAnthropic

        self._client = AsyncAnthropic()
        self._model = model

    async def generate_sql(self, question: str) -> str:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=400,
            system=SCHEMA_PROMPT,
            messages=[{"role": "user", "content": question}],
        )
        text = "".join(block.text for block in response.content if block.type == "text").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if "\n" in text:
                first_line, rest = text.split("\n", 1)
                text = rest if first_line.strip().lower() in ("", "sql") else text
        return text.strip()


class StubAskLlm:
    """Deterministic offline stand-in — recognises a couple of question
    shapes, otherwise falls back to a safe default. Good enough to exercise
    the guardrail plumbing without an API key, in dev and in CI."""

    async def generate_sql(self, question: str) -> str:
        q = question.lower()
        if "top" in q or "best" in q or "product" in q:
            return (
                "SELECT product_name, SUM(line_total) AS revenue FROM orders "
                "GROUP BY product_name ORDER BY revenue DESC LIMIT 5"
            )
        if "order" in q and ("count" in q or "how many" in q):
            return "SELECT COUNT(DISTINCT order_id) AS order_count FROM orders"
        return (
            "SELECT DATE(placed_at) AS day, SUM(line_total) AS revenue FROM orders "
            "GROUP BY day ORDER BY day"
        )


def create_ask_llm(kind: str, model: str) -> AskLlm:
    if kind == "anthropic":
        return AnthropicAskLlm(model)
    return StubAskLlm()
