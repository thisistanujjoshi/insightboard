# Deploy story

## Local: docker compose

```bash
docker compose build
docker compose up -d
```

| Service | Image | Host port | Backing store |
|---|---|---|---|
| `data-service` | `insightboard/data-service` | 8000 | PostgreSQL (warehouse) + Elasticsearch (product search) |
| `dashboard` | `insightboard/dashboard` (nginx, static build) | 5175 | — (calls data-service) |
| `admin` | `insightboard/admin` | 5256 | SQLite (tenant registry — a config store, not the warehouse; same "vary the data store" choice as NexusCommerce's Catalog service) |
| `postgres` | `postgres:17-alpine` | — (internal) | — |
| `elasticsearch` | `elasticsearch:8.15.0` | — (internal) | — |

All credentials in `docker-compose.yml` are dev-only. A real deployment
would inject them from a secrets manager rather than hardcoding them, the
same way NexusCommerce's Helm chart pulls from Key Vault.

## Feature flags

`data-service` exposes `GET /api/v1/features`; the dashboard reads it once
on load and hides the corresponding UI if a flag is off. Both flags are
**kill switches**, not experiment flags — flip them via env var, no
redeploy, no code change:

| Env var | Default | Effect when `false` |
|---|---|---|
| `INSIGHT_FEATURE_ASK` | `true` | `POST /ask` returns 404; the dashboard hides the Ask-in-English box |
| `INSIGHT_FEATURE_FORECAST` | `true` | `/forecast` and `/anomalies` return 404; the chart shows actuals only |

This exists specifically for the PRD's own risk callout on Ask-in-English
("LLM writes bad SQL") — if a guardrail gap turns up in the field, ops can
disable the feature in seconds instead of waiting on a deploy.

## Ask-in-English: known limitation on PostgreSQL

The NL→SQL guardrail (`app/nlsql.py`) materialises a tenant-scoped temp
table and flips the connection to `PRAGMA query_only` — a SQLite-specific
mechanism. Run `data-service` against PostgreSQL (as `docker-compose.yml`
does) and `POST /ask` returns `501 Not Implemented` with that explained
in the response body; every other endpoint (ingest, summary, forecast,
search, feedback) works the same against Postgres as it does against
SQLite, since only `nlsql.py`'s raw connection path is SQLite-only.

The equivalent Postgres mechanism is well understood — a dedicated
read-only DB role (`GRANT SELECT` only, no `INSERT`/`UPDATE`/`DELETE`) plus
`SET statement_timeout` at the session level — but wiring it up is tracked
as a follow-up (`docs/backlog.md` icebox) rather than bundled into this
sprint's Docker/CI/flags scope.

## Path to a real cluster

InsightBoard ships as three containers and a docker-compose file — enough
to run the whole platform on one host. For a real multi-node deployment,
reuse OpsForge's Terraform modules (network/AKS/ACR/Key Vault/Postgres) and
Helm chart pattern instead of hand-rolling new infra per project: point the
same module set at InsightBoard's three images, add a Postgres module
instance for the warehouse, and an Elasticsearch/managed-search instance in
place of the local container. That reuse — one platform foundation, N
applications — is the whole point of building OpsForge second.
