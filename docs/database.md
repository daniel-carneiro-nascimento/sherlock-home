# Local Database

## Current implementation

Sherlock Home currently uses PostgreSQL as its local relational database.

The reference development setup runs PostgreSQL in Docker and binds the host port to `127.0.0.1`, avoiding exposure on LAN interfaces.

Application access is implemented with SQLAlchemy 2 and the `psycopg` driver. Schema migrations are managed by Alembic.

## Main files

```text
app/db/base.py
app/db/database.py
app/models/transaction.py
alembic/
alembic.ini
```

## Transaction model

The current transaction schema stores the canonical fields needed by the ingestion foundation, including:

- transaction date
- original description
- decimal amount
- optional merchant
- optional card
- optional category
- optional installment position/total
- statement month
- creation timestamp
- unique transaction fingerprint

Money uses PostgreSQL `NUMERIC` and Python `Decimal`. Binary floating point must not be used for persisted monetary amounts.

## Fingerprints

`app/ingestion/fingerprint.py` generates a SHA-256 fingerprint from canonical transaction properties plus an occurrence index.

The occurrence index matters because two legitimate transactions can otherwise be identical: same date, same amount, same description, and no document number.

Canonical fingerprint inputs currently include:

```text
date
amount
normalized whitespace in description
document or empty value
statement month
occurrence index
```

## Idempotent import

`app/ingestion/importer.py` checks the unique fingerprint before adding a transaction.

Expected behavior:

```text
first import:
N inserted
0 skipped

same statement imported again:
0 inserted
N skipped
```

The database also enforces uniqueness through a unique constraint on the fingerprint column. Application checks improve behavior and reporting; the database constraint remains the final duplicate barrier.

## Credentials

Database credentials come from local configuration and must not enter LLM context, documentation examples containing real values, tests, or Git history.
