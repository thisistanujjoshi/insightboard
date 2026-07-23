"""Guardrails for the Ask-in-English feature.

The PRD's stated risk: "LLM writes bad SQL." The mitigation is structural,
not prompt-based — the model is never shown a `tenant_id` column and never
told which tenant it's answering for. Instead:

1. `run_readonly_query` builds a per-tenant temp TABLE named `orders`,
   materialised via `CREATE TEMP TABLE ... AS SELECT ... WHERE tenant_id = ?`
   — tenant_id is bound as a real query parameter (never string-interpolated
   into SQL the model can influence). SQLite views can't take bound
   parameters, which is why this is a materialised table rather than a view;
   the model only ever sees this one table, never `order_lines` itself.
2. `validate_sql` whitelists the `orders` table, blocklists write/DDL
   keywords, rejects multi-statement input and CTEs, and rejects any query
   that references `tenant_id` at all (a model that tries has no legitimate
   reason to, since the table is already scoped).
3. `run_readonly_query` ALSO opens its connection in `PRAGMA query_only`
   mode and installs a wall-clock progress handler — defense in depth, so a
   bug in `validate_sql` still can't produce a write or a runaway query.
"""

import re
import sqlite3
import time
from typing import Callable

ALLOWED_VIEW = "orders"
DEFAULT_MAX_ROWS = 200
DEFAULT_TIMEOUT_SECONDS = 5.0

_FORBIDDEN_KEYWORDS = (
    "insert", "update", "delete", "drop", "alter", "create", "attach",
    "detach", "pragma", "replace", "truncate", "grant", "revoke", "vacuum",
    "reindex", "exec", "execute",
)
_TABLE_REF = re.compile(r"\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)", re.IGNORECASE)
_TRAILING_LIMIT = re.compile(r"\blimit\s+(\d+)\s*$", re.IGNORECASE)


class UnsafeQueryError(Exception):
    """The SQL failed a guardrail — either our own validator, or the
    database itself rejecting a write it should never have been asked to
    perform."""


class QueryTimeoutError(Exception):
    """The query ran past its wall-clock budget and was interrupted."""


def validate_sql(sql: str) -> str:
    """Returns the trimmed statement if it's a safe read against the
    tenant-scoped view; raises UnsafeQueryError otherwise."""
    trimmed = sql.strip()
    if not trimmed:
        raise UnsafeQueryError("Empty query.")

    body = trimmed[:-1].strip() if trimmed.endswith(";") else trimmed
    if ";" in body:
        raise UnsafeQueryError("Multiple statements are not allowed.")

    lowered = body.lower()
    if not lowered.startswith("select"):
        # CTEs (WITH ...) are deliberately unsupported: this validator finds
        # table references with a regex, not a real SQL parser, and can't
        # safely tell a CTE-scoped name apart from a real table — so it
        # can't be sure a `WITH` query only reaches the `orders` table.
        raise UnsafeQueryError("Only plain SELECT queries are allowed (no WITH/CTEs).")

    for keyword in _FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", lowered):
            raise UnsafeQueryError(f"Disallowed keyword: {keyword}")

    if re.search(r"\btenant_id\b", lowered):
        raise UnsafeQueryError("Query must not reference tenant_id directly.")

    tables = {m.group(1).lower() for m in _TABLE_REF.finditer(body)}
    disallowed = tables - {ALLOWED_VIEW}
    if disallowed:
        raise UnsafeQueryError(
            f"Query may only select from '{ALLOWED_VIEW}': found {sorted(disallowed)}"
        )

    return body


def enforce_row_limit(sql: str, max_rows: int = DEFAULT_MAX_ROWS) -> str:
    """Caps (or adds) a trailing LIMIT so one query can't pull the whole
    warehouse — the PRD's "cost cap" guardrail."""
    match = _TRAILING_LIMIT.search(sql)
    if match:
        existing = int(match.group(1))
        if existing <= max_rows:
            return sql
        return sql[: match.start()] + f"LIMIT {max_rows}"
    return f"{sql}\nLIMIT {max_rows}"


def run_readonly_query(
    raw_connect: Callable[[], sqlite3.Connection],
    tenant_id: str,
    sql: str,
    *,
    max_rows: int = DEFAULT_MAX_ROWS,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> list[dict]:
    conn = raw_connect()
    try:
        conn.row_factory = sqlite3.Row
        conn.execute(
            "CREATE TEMP TABLE orders AS "
            "SELECT order_id, placed_at, product_sku, product_name, quantity, "
            "unit_price, quantity * unit_price AS line_total "
            "FROM order_lines WHERE tenant_id = ?",
            (tenant_id,),
        )
        # Flip to read-only AFTER materialising the tenant-scoped table:
        # query_only covers the temp database too, so this also blocks any
        # attempt to write to `orders` itself, not just `order_lines`.
        conn.execute("PRAGMA query_only = ON")

        start = time.monotonic()

        def handler() -> int:
            return 1 if (time.monotonic() - start) > timeout_seconds else 0

        conn.set_progress_handler(handler, 1000)
        try:
            cursor = conn.execute(sql)
            rows = [dict(row) for row in cursor.fetchall()][:max_rows]
        except sqlite3.OperationalError as exc:
            message = str(exc).lower()
            if "interrupted" in message:
                raise QueryTimeoutError(
                    f"Query exceeded {timeout_seconds:.1f}s and was stopped."
                ) from exc
            raise UnsafeQueryError(f"The database rejected this query: {exc}") from exc
        finally:
            conn.set_progress_handler(None, 0)
        return rows
    finally:
        conn.close()
