# InsightBoard — Product Requirements (one page)

**Author:** Tanuj Joshi · **Date:** 2026-07-23 · **Status:** Approved for build

## Problem

Small online-shop operators (10–500 orders/day) make pricing and stock decisions
on gut feel. Their platforms (Shopify-likes, custom shops like NexusCommerce)
capture rich order data but surface it as CSV exports. Hiring an analyst isn't
realistic; existing BI tools (Metabase, Power BI) assume someone can model data
and write queries. Result: stockouts on best-sellers, dead capital in slow
movers, and promotions timed by instinct.

## Solution

InsightBoard is a multi-tenant analytics SaaS that connects to a shop's order
stream and answers the three questions operators actually ask — *what's
selling, what's about to run out, what changed* — plus a fourth they can't ask
anywhere else: **anything, in plain English** ("which products slowed down
after the price change in June?"), answered by an LLM that writes the SQL and
returns a chart.

## Users & jobs (see personas.md)

- **Shop owner (primary):** glanceable revenue/stock dashboard; plain-English questions; zero setup.
- **Ops analyst (secondary):** anomaly alerts, forecast horizon for reordering, drill-down.
- **InsightBoard admin (internal):** tenant onboarding, plan/billing state, usage.

## Scope — v1

| # | Capability | Notes |
|---|---|---|
| 1 | Tenant back office | Create/manage tenants, plans (Free/Pro), suspend; internal-facing (ASP.NET MVC) |
| 2 | Ingest + warehouse | Order events → PostgreSQL star-ish schema; Elasticsearch for product search |
| 3 | Dashboard | Revenue/orders/top-products charts, per-tenant isolation, React SPA |
| 4 | Forecasting & anomalies | 14-day revenue forecast; daily anomaly flags (scikit-learn) |
| 5 | Ask-in-English | NL → SQL via LLM, read-only, tenant-scoped, chart or table answer |
| 6 | Feedback widget | In-app thumbs + comment, feeds the backlog; one A/B test on its placement |

**Out of scope v1:** self-serve signup, payments processing (plan state only),
email digests, multi-currency, mobile apps.

## Success metrics (90 days post-launch)

- ≥ 60% of weekly-active tenants use Ask-in-English at least once
- Forecast MAPE ≤ 25% on tenants with ≥ 60 days of history
- Time from tenant creation to first rendered chart ≤ 10 minutes
- ≥ 20 feedback submissions (widget A/B test decides placement)

## Risks

- **LLM writes bad SQL** → read-only DB role, per-tenant row scoping enforced
  outside the prompt, query timeout + cost cap, show the SQL for trust.
- **Sparse tenant data** → forecasts degrade gracefully to moving averages
  below a history threshold; label confidence.
- **Tenant data isolation** — every query path carries tenant_id server-side;
  verified by tests before launch (phase 4 gate).
