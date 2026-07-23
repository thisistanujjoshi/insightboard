# InsightBoard

An AI-augmented, multi-tenant analytics SaaS for small online shops: a
server-rendered back office for tenant management, a Python data API over a
PostgreSQL warehouse + Elasticsearch, a React dashboard, scikit-learn
forecasting, and a natural-language "ask a question, get a chart" feature.

**Product-first:** this project starts from a written [PRD](docs/PRD.md),
[personas](docs/personas.md), and a [sprint backlog](docs/backlog.md) — the
build follows the backlog, and in-app feedback feeds back into it.

## Architecture (planned)

| Piece | Stack | Why |
|---|---|---|
| Admin back office | ASP.NET Core **MVC** (Razor views) | Server-rendered CRUD for internal users — deliberately the MVC pattern, vs project 1's API controllers and OpsForge's minimal API |
| Data service | Python FastAPI | Order ingest, warehouse queries, NL→SQL |
| Warehouse | PostgreSQL + Elasticsearch | Relational analytics + product search |
| ML | scikit-learn / pandas | 14-day forecast, daily anomaly flags |
| Dashboard | React + TypeScript | Charts + feedback widget (A/B tested) |
| LLM | Claude API | English → guarded, read-only, tenant-scoped SQL |

## Build phases

- [ ] **1** — PRD/personas/backlog ✅ · MVC back office with tenant model
- [ ] **2** — Data API + warehouse + React dashboard
- [ ] **3** — Forecasting/anomalies + feedback widget + A/B test
- [ ] **4** — Ask-in-English (NL→SQL) + role-based authorization
- [ ] **5** — Docker, CI/CD, feature flags, deploy

Part of a 3-project portfolio with
[nexuscommerce](https://github.com/thisistanujjoshi/nexuscommerce) and
[opsforge](https://github.com/thisistanujjoshi/opsforge).
