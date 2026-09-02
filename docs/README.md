# Sherlock Home Documentation

This directory contains implementation-oriented documentation for Sherlock Home.

The root `README.md` describes the project at a high level. The files here document specific subsystems and flows so that implementation details can evolve without turning the project README into a monolith.

## Documentation map

- [`architecture.md`](architecture.md) — overall architecture and design principles.
- [`financial-data-flow.md`](financial-data-flow.md) — current financial ingestion flow from local statement to PostgreSQL.
- [`database.md`](database.md) — local PostgreSQL, SQLAlchemy, Alembic, transaction schema, fingerprints, and idempotency.
- [`data-safety.md`](data-safety.md) — handling rules for real financial statements and extracted text.
- [`testing.md`](testing.md) — synthetic fixtures, parser tests, integration tests, and safety rules.
- [`parsers/README.md`](parsers/README.md) — parser architecture and the contract for bank-specific parsers.
- [`parsers/santander.md`](parsers/santander.md) — implemented Santander PDF parser.

## Documentation principle

Bank-specific parsing logic must remain isolated from the canonical transaction model whenever practical.

A bank can change its PDF, CSV, or OFX layout independently of other banks. Keeping one parser per bank/source format means a layout change should normally require modifying only that parser and its fixtures/tests, not the database schema or unrelated parsers.
