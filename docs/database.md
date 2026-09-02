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
- transaction type (`expense`, `income`, or `transfer`)
- optional card
- optional expense category
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
source
source type
source account
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


## Derived fields and identity

`merchant`, `transaction_type`, and `category` are deterministic derived fields.

They are persisted for later financial analysis, but they are intentionally excluded from the transaction fingerprint. Improving a merchant alias, movement-type rule, or category rule must not cause the same source transaction to appear as a new transaction.

Current semantic split:

```text
transaction_type:
  expense
  income
  transfer

expense category:
  food
  groceries
  transport
  utilities
  health
  shopping
  housing
  financing
  leisure
  taxes
  None
```

Only `expense` movements are eligible for expense categorization.

## Test database isolation

Database integration tests use a separate PostgreSQL database:

```text
POSTGRES_DB=sherlock_home
POSTGRES_TEST_DB=sherlock_home_test
```

The pytest fixtures in `tests/conftest.py` fail closed if the test database matches the application database or if the configured test database does not end in `_test`.

The test database is disposable and may be cleaned between tests. The normal application database must never be reset by the test suite.

Schema changes to the application database continue to use Alembic. The disposable test database is created from SQLAlchemy metadata for test execution.


## Runtime configuration tables

v0.5.0 adds persistent deterministic rule configuration to PostgreSQL.

### `merchant_aliases`

Stores locally managed merchant canonicalization rules.

Conceptual fields:

```text
id
canonical_name
pattern
priority
enabled
```

`priority` is unique so rule ordering is deterministic. Disabled rules remain persisted but are ignored by the runtime loader.

### `category_rules`

Stores locally managed expense-category rules.

Conceptual fields:

```text
id
category
field
pattern
priority
enabled
```

The service validates the persisted category and rule field against the canonical enums before compiling the regex.

### Runtime loaders

```text
app/services/merchant_aliases.py
app/services/category_rules.py
```

read enabled rows in deterministic priority order.

The orchestration service:

```text
app/services/financial_pipeline.py
```

uses those loaders before merchant normalization and expense categorization.

These tables are intended to become the persistence layer behind the local web configuration UI.

## Configuration boundary

`.env` is reserved for operational configuration:

```text
database connectivity
local AI runtime
application environment
service endpoints
```

Household financial rules and aliases are persisted in PostgreSQL. They are not expected to require direct `.env` editing.

