# Local Web Hosting — F1 Prototype

This is the first server-rendered Sherlock Home web interface.

It deliberately avoids a JavaScript frontend framework.

## Stack

```text
FastAPI
Jinja2
server-rendered HTML
plain CSS
Matplotlib-generated SVG charts
PostgreSQL
existing Sherlock Home server-side sessions
```

No React, Vue, Angular, Plotly browser runtime, or custom JavaScript is required for this iteration.

## Why server-rendered Python first?

Sherlock Home already has:

- FastAPI;
- secure server-side sessions;
- CSRF protection;
- PostgreSQL;
- deterministic financial services;
- local financial analysis tools.

The first frontend therefore reuses the backend directly rather than adding a second application runtime.

Charts are generated as SVG by Python on the server.

## Install the web dependencies

After extracting the package at repository root, run the temporary helper:

```bash
python .tmp/scripts/enable_web_dependencies.py
pip install -e ".[dev,web]"
```

The helper modifies `pyproject.toml` and is intentionally stored under `.tmp/`.

## Run

The existing Sherlock Home security model requires HTTPS because authentication uses `__Host-` Secure cookies.

Start the web entrypoint with:

```bash
python -m scripts.run_web_https
```

Then open:

```text
https://127.0.0.1:8443/web/login
```

Use an existing Sherlock Home account.

## Current dashboard data

The dashboard selects the latest transaction month available in PostgreSQL.

This means the existing synthetic June/July 2026 data can be used immediately. If July 2026 is the latest month, the dashboard will show July and compare it with June.

The dashboard uses existing deterministic services for:

- monthly spending;
- monthly comparison;
- category spending;
- cash flow;
- recurring expenses;
- anomalies;
- duplicate charges.

## Presentation settings

The Settings screen currently supports:

```text
Theme
  Light
  Dark

Chart colors
  Standard
  Red/green-safe
  Blue/yellow-safe

Dashboard density
  Balanced
  Compact
  More space for analysis
```

These values are presentation-only cookies. They contain no financial data.

The chart colors are rendered by Python/Matplotlib and the interface does not use color as the only indicator.

## Dashboard customization boundary

The dashboard is deliberately not modular.

Users do not construct arbitrary graphs from arbitrary metrics.

Instead, Sherlock Home owns the available panels and allows controlled layout preferences such as density and relative emphasis.

This preserves a coherent household-finance experience and avoids turning the product into a generic Grafana clone.

## Admin support

The current public backend has `admin` and `user` roles in a single-household model.

This prototype therefore exposes:

```text
/web/admin
```

Admins can see the current users and choose **Visualizar como**.

This is intentionally a **support preview**, not full identity impersonation. The admin remains the authenticated actor.

A real impersonation capability must later use a server-side auditable support session containing at least:

- administrator actor;
- target user;
- household;
- start time;
- stop time;
- explicit support reason;
- audit event.

The frontend must not use a hidden browser-only identity override.

## User identity follow-up

The current public backend user table is username-based and the current backend password validator requires 12 characters.

The approved frontend direction changes account identity to include:

- email;
- full name;
- password with a minimum length of 8 characters;
- no mandatory number or symbol requirement.

That change is intentionally **not smuggled into this hosting prototype** because it requires an explicit database/authentication migration and updates to the existing authentication test contract.

It should be implemented as the next identity/household backend slice before real multi-user household sharing.

## Single-household limitation

The current backend migration explicitly establishes a single-household user/session foundation.

The dashboard therefore labels the data as a local shared household base but does not pretend that transactions are already scoped per user.

Per-user financial visibility requires explicit ownership/sharing relations in the backend.
