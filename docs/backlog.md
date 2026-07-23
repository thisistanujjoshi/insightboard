# Backlog & sprint plan

Kanban: **Backlog → Sprint → In progress → Review → Done.** Two-week sprints;
retro note per sprint in `docs/retros/`. Feedback-widget submissions land here
as new backlog rows tagged `[feedback]`.

## Epics → phases

| Epic | Phase | Definition of done |
|---|---|---|
| E1 Product docs + tenant back office | 1 | PRD approved; MVC admin CRUDs tenants/plans with tests |
| E2 Warehouse + dashboard | 2 | Order data queryable; React dashboard renders real tenant charts |
| E3 Forecasting + feedback loop | 3 | Forecast endpoint with accuracy note; widget live + A/B assignment |
| E4 Ask-in-English + authz | 4 | NL→SQL behind read-only scoped role; tenant isolation test gate |
| E5 Ship | 5 | Docker, CI/CD, feature flags, deploy story |

## Sprint 1 (current)

- [x] PRD one-pager
- [x] Personas
- [x] Backlog + sprint structure
- [x] Solution scaffold: ASP.NET Core MVC admin (Razor), layered like the CV expects
- [x] Tenant + Plan model, EF Core, seeded demo tenants
- [x] Tenant list/create/edit/suspend views + validation + tests
- [x] CI on push

## Sprint 2 (planned)

- [x] FastAPI data service: order ingest + PostgreSQL warehouse schema
- [x] Elasticsearch product index + search endpoint
- [x] React dashboard shell: revenue, orders, top products (per tenant)
- [x] Demo data generator (NexusCommerce-shaped orders)

## Sprint 3 (current)

- [x] Forecast endpoint: scikit-learn trend model, moving-average fallback under 21 days, confidence label
- [x] Anomaly detection: trailing moving-average baseline + z-score flagging
- [x] Dashboard: forecast overlay (dashed projection) + anomaly markers on the revenue chart
- [x] Feedback widget with sidebar/footer A/B placement test, backed by `/feedback` + `/feedback/stats`

## Sprint 4 (planned)

- [ ] Ask-in-English: LLM translates plain English to read-only, tenant-scoped SQL
- [ ] Role-based authorization; tenant data isolation test gate

## Icebox

- Email digests · self-serve signup · multi-currency · saved questions
