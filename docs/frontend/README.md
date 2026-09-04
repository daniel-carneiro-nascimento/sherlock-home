# Sherlock Home Frontend Documentation

This directory contains the planning and architecture documentation for the Sherlock Home household-facing web interface.

The frontend roadmap is intentionally separate from the backend/application roadmap.

## Documents

- [`architecture.md`](architecture.md) — approved frontend product and technical architecture direction.
- [`ROADMAP.md`](ROADMAP.md) — frontend-only implementation phases and Holmes-Hat web release gate.

## Current Status

The frontend **concept and architecture direction are approved**, including:

- light and dark modes;
- friendly Sherlock Home detective-boy mascot direction;
- dashboard composition;
- household-oriented financial language;
- individual and shared financial goals;
- shared-account presentation concept;
- chart accessibility modes;
- Sherlock chat and evidence flow;
- frontend/backend responsibility separation.

The frontend itself is **not yet implemented**.

The next implementation frontier is:

```text
F1 — Web Shell and Authenticated Navigation
```

## Backend Documentation

Backend/application architecture and roadmap remain separate:

- [`../architecture.md`](../architecture.md)
- [`../ROADMAP.md`](../ROADMAP.md)
- [`../API_V1.md`](../API_V1.md)

## Design Principle

The browser presents financial information.

The backend remains authoritative for:

- financial calculations;
- persistence;
- authentication;
- authorization;
- CSRF;
- security policy;
- tool execution;
- local AI orchestration;
- protected-data handling.
