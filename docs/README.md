# Sherlock Home Documentation

Sherlock Home is documented as a **single-household, local-first system**. It is not a public SaaS or multi-tenant platform.

Current documented milestone: **v0.5.0**.

This directory contains implementation-oriented documentation for Sherlock Home.

The root `README.md` describes the project at a high level. The files here document specific subsystems and flows so that implementation details can evolve without turning the project README into a monolith.

## Documentation map

- [`ROADMAP.md`](ROADMAP.md) — project phases, status, and current development frontier.
- [`architecture.md`](architecture.md) — overall architecture and design principles.
- [`financial-data-flow.md`](financial-data-flow.md) — current parser, canonical normalization, PostgreSQL-backed merchant/category enrichment, transaction typing, fingerprint, persistence, and analysis boundary.
- [`financial-tools.md`](financial-tools.md) — Phase 5 deterministic financial-analysis contracts and implementation order.
- [`database.md`](database.md) — local PostgreSQL, SQLAlchemy, Alembic, transaction schema, runtime rule tables, test-database isolation, fingerprints, and idempotency.
- [`API_V1.md`](API_V1.md) — authenticated API contract.
- [`PRIVATE_HTTPS_DEPLOYMENT.md`](PRIVATE_HTTPS_DEPLOYMENT.md) — private HTTPS deployment model.
- [`data-safety.md`](data-safety.md) — handling rules for real financial statements and extracted text.
- [`testing.md`](testing.md) — behavior-oriented tests, taxonomy/rule tests, database isolation, integration tests, and safety rules.
- [`parsers/README.md`](parsers/README.md) — parser architecture and the contract for bank-specific parsers.
- [`parsers/santander.md`](parsers/santander.md) — implemented Santander PDF parser.

## Documentation principle

Bank-specific parsing logic must remain isolated from the canonical transaction model whenever practical.

A bank can change its PDF, CSV, or OFX layout independently of other banks. Keeping one parser per bank/source format means a layout change should normally require modifying only that parser and its fixtures/tests, not the database schema or unrelated parsers.

## Current financial boundary

```text
bank-specific ingestion
    ↓
canonical normalization
    ↓
deterministic enrichment
    ↓
fingerprint / idempotent persistence
    ↓
PostgreSQL
    ↓
deterministic financial tools
```

`transaction_type` and `category` are deliberately separate. `expense`, `income`, and `transfer` describe movement nature; expense categories describe spending purpose.

The current implementation frontier is Phase 5, beginning with deterministic monthly-spending analysis.

## Releases

- [`releases/v0.5.0.md`](releases/v0.5.0.md) — deterministic financial ingestion and PostgreSQL-backed local enrichment checkpoint.
