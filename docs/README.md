# Sherlock Home Documentation

This directory contains implementation-oriented documentation for Sherlock Home.

The root `README.md` describes the project at a high level. The files here document specific subsystems and flows so that implementation details can evolve without turning the project README into a monolith.

## Documentation map

- [`architecture.md`](architecture.md) — overall architecture and design principles.
- [`financial-data-flow.md`](financial-data-flow.md) — current parser, canonical normalization, merchant normalization, transaction typing, expense categorization, fingerprint, and persistence flow.
- [`database.md`](database.md) — local PostgreSQL, SQLAlchemy, Alembic, transaction schema, derived fields, test-database isolation, fingerprints, and idempotency.
- [`data-safety.md`](data-safety.md) — handling rules for real financial statements and extracted text.
- [`testing.md`](testing.md) — behavior-oriented tests, taxonomy/rule tests, database isolation, integration tests, and safety rules.
- [`parsers/README.md`](parsers/README.md) — parser architecture and the contract for bank-specific parsers.
- [`parsers/santander.md`](parsers/santander.md) — implemented Santander PDF parser.

## Documentation principle

Bank-specific parsing logic must remain isolated from the canonical transaction model whenever practical.

A bank can change its PDF, CSV, or OFX layout independently of other banks. Keeping one parser per bank/source format means a layout change should normally require modifying only that parser and its fixtures/tests, not the database schema or unrelated parsers.


## Current financial enrichment boundary

After a bank-specific parser produces parsed transactions, generic deterministic stages handle the financial semantics:

```text
statement normalization
    ↓
merchant normalization
    ↓
transaction typing
    ↓
expense categorization
    ↓
fingerprint / idempotent persistence
```

`transaction_type` and `category` are deliberately separate. `expense`, `income`, and `transfer` describe movement nature; expense categories describe spending purpose.
