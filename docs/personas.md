# Personas

## Priya — shop owner (primary)

Runs a 3-person electronics shop doing ~120 orders/day on a custom platform.
Checks her phone between packing orders. Spreadsheet-literate, query-illiterate.

- **Wants:** "am I having a good week?", "what do I reorder Friday?"
- **Buys when:** the first dashboard renders without her configuring anything.
- **Churns when:** numbers disagree with her gut and she can't ask *why*.
- **Design consequences:** defaults over settings; plain-English querying is for
  her; every chart answers a question she'd phrase aloud.

## Marco — operations analyst (secondary)

Part-time analyst at a 40-person retailer with 6 storefront tenants. Knows SQL
but spends his day in tickets. Trusts numbers only when he can see the workings.

- **Wants:** anomaly flags before customers complain; forecast horizon aligned
  to supplier lead times; the SQL behind any AI answer.
- **Design consequences:** show-your-work on NL→SQL (display generated SQL);
  export; per-tenant switcher.

## Dana — InsightBoard admin (internal)

Runs onboarding and support for InsightBoard itself.

- **Wants:** create/suspend tenants fast, see plan + usage at a glance, audit
  who changed what.
- **Design consequences:** the MVC back office is a dense, boring, fast CRUD
  tool — server-rendered tables over SPA polish.
