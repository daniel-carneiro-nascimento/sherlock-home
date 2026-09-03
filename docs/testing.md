# Sherlock Home Testing Strategy

Sherlock Home uses deterministic, behavior-oriented tests for security, ingestion, normalization, identity, and persistence.

The test suite is designed to validate **rules and invariants**, not memorize one synthetic financial statement.

---

## Core Principle

The central testing rule is:

```text
Fixtures describe structure.
Parameterized tests exercise classes of values.
Invariant tests verify behavior.
```

A synthetic statement fixture is not a "golden" financial record.

Changing a synthetic balance or transaction amount should not require changing unrelated structural tests. If a test fails only because a fixture changed from one valid monetary value to another valid monetary value, that test is probably coupled to fixture data rather than to the parser rule it intends to verify.

---

## Why Sherlock Home Does Not Use Golden Financial Values

A financial parser must work with arbitrary valid statement values.

For example, all of the following may be valid Brazilian monetary representations:

```text
23,50-
79,52-
500,00
1.250,00
1.234,56-
9.999,99-
1.234.567,89
```

A test that proves only that one hard-coded balance parses correctly does not establish that the monetary parser handles the format generally.

Instead, value parsing is tested with parameterized synthetic inputs and deterministic `Decimal` results.

The question should be:

```text
Does the parser correctly implement this class of input?
```

not:

```text
Does the parser still remember the numbers currently stored in the fixture?
```

---

## Structural Fixtures

Files under `tests/fixtures/` reproduce relevant source layout while containing only synthetic data.

A structural fixture may preserve:

- exact or representative column spacing
- statement header wording
- date placement
- debit/credit notation
- repeated table headers
- multiline descriptions
- missing document fields
- missing per-row balances
- section boundaries
- page-layout behavior relevant to parsing

The fixture must not preserve real:

- account numbers
- bank document identifiers
- transaction identifiers
- merchant data that can map back to a real statement
- balances
- transaction amounts
- personal information

The principle is:

```text
Keep the format.
Replace the data.
```

Fixtures are allowed to change synthetic values without becoming different "truth sets" for the parser.

---

## Santander Parser Tests

`tests/test_santander_pdf.py` separates structural parsing from value parsing.

### Structural behavior

The synthetic statement fixture is used to verify behavior such as:

- the statement period is detected
- transactions are discovered from the intended section
- parsed transactions contain dates and `Decimal` amounts
- descriptions are non-empty
- multiline descriptions are joined
- transactions without an explicit date inherit the previous valid transaction date
- repeated headers do not become transactions
- parsing stops at the intended movement-section boundary
- malformed or suspicious structures fail closed

These assertions describe parser behavior, not one fixture's arbitrary financial values.

### Monetary behavior

Brazilian monetary parsing is tested independently using parameterized values.

Conceptually:

```python
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("23,50-", Decimal("-23.50")),
        ("500,00", Decimal("500.00")),
        ("1.234,56-", Decimal("-1234.56")),
    ],
)
def test_parse_brazilian_decimal(raw, expected):
    assert parse_brazilian_decimal(raw) == expected
```

Full synthetic transaction lines may also be generated inside parameterized tests when the interaction between layout, movement values, and balances must be verified.

---

## Normalization Tests

`tests/test_normalization.py` verifies the contract between source-specific parser output and Sherlock Home's canonical financial representation.

Normalization tests focus on invariants.

Examples:

```text
amount is preserved
date is preserved
document is preserved when present
description whitespace is canonicalized
source is set to "santander"
source_type is set to "bank_statement"
source_account is preserved
```

Amounts should be tested with multiple synthetic `Decimal` values rather than a single fixture-specific amount.

The normalization layer may canonicalize representation, but it must not silently alter financial meaning.

---

## Merchant Normalization Tests

`tests/test_merchant_normalization.py` verifies deterministic merchant enrichment.

The tests establish that:

- recognized patterns produce normalized merchant names
- whitespace normalization is deterministic
- unknown patterns remain `None`
- financial fields are preserved
- statement-level enrichment does not mutate unrelated canonical metadata

The merchant normalizer must not guess when no deterministic rule matches.

---

## Transaction Typing Tests

`tests/test_transaction_typing.py` and `tests/test_transaction_type_rules.py` verify the movement-type taxonomy:

```text
expense
income
transfer
```

Tests cover explicit description rules, amount-sign fallback behavior, deterministic rule priority, custom rule injection, and preservation of canonical transaction data.

The typing layer answers **what kind of financial movement occurred**.

---

## Expense Categorization Tests

`tests/test_expense_categorization.py` and `tests/test_category_rules.py` verify the expense-purpose taxonomy and its rule engine.

The current taxonomy is:

```text
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
```

Tests verify:

- taxonomy values are unique
- rule priorities are unique and sorted
- every category has at least one rule
- known synthetic merchants/descriptions map deterministically
- unknown merchants remain uncategorized
- rule priority resolves overlapping matches deterministically
- non-expense transactions are never assigned an expense category
- categorization preserves transaction type and financial data

In this case, exact taxonomy strings are valid fixed expectations because the taxonomy itself is the rule being tested. This differs from a fixture-specific monetary value, which is merely one sample input.

---

## PostgreSQL Rule Configuration Tests

The v0.5.0 suite validates persistent financial enrichment configuration.

Relevant tests cover:

```text
category rule persistence
merchant alias persistence
enabled/disabled filtering
priority ordering
database rule override behavior
runtime pipeline integration
```

The tests use only the isolated `sherlock_home_test` database.

The `db_session` fixture cleans all mutable integration-test tables before and after each test:

```text
transactions
category_rules
merchant_aliases
```

This prevents one test's persisted rules from affecting the next test and preserves the fail-closed boundary protecting the normal application database.

---

## Runtime Financial Pipeline Tests

`tests/test_financial_pipeline.py` verifies that the production-oriented orchestration layer actually consumes PostgreSQL configuration.

The tests establish that:

- merchant aliases stored in PostgreSQL affect merchant normalization
- category rules stored in PostgreSQL affect expense categorization
- database rules can deterministically override broader defaults through priority
- disabled rules are ignored
- Santander parser output can pass through the complete runtime enrichment path
- income remains uncategorized
- derived fields preserve the source financial data

The importer integration test uses the same runtime preparation service rather than assembling enrichment stages independently.

This is important because the tested pipeline and the intended application pipeline now share the same orchestration boundary.

---

## Fingerprint Tests

`tests/test_fingerprint.py` verifies deterministic transaction identity.

Tests should not hard-code the literal SHA-256 output.

The behavior under test is relational:

```text
same canonical identity + same occurrence
    => same fingerprint

different occurrence
    => different fingerprint

different identity attribute
    => different fingerprint
```

Relevant identity attributes currently include:

- transaction date
- amount
- canonical description
- document
- statement month
- source
- source type
- source account
- occurrence index

This tests the fingerprint contract without coupling the suite to an opaque hash literal.

---

## Importer Tests

`tests/test_importer.py` verifies idempotent persistence.

The test derives its expected transaction count from the normalized statement:

```python
expected_count = len(statement.transactions)
```

It should not contain an assertion such as:

```python
assert inserted == 4
```

merely because the current fixture happens to contain four transactions.

The property being tested is:

```text
First import:
    inserted = expected_count
    skipped = 0

Second import:
    inserted = 0
    skipped = expected_count
```

That property remains valid if the synthetic fixture later changes size for legitimate structural reasons.

The importer integration test also verifies that derived `merchant`, `transaction_type`, and `category` values are persisted without becoming part of the fingerprint identity.

---

## Database Integration Test Isolation

Persistence tests must never use the normal application database.

The test configuration separates:

```text
POSTGRES_DB=sherlock_home
POSTGRES_TEST_DB=sherlock_home_test
```

`tests/conftest.py` provides a dedicated SQLAlchemy engine and `db_session` fixture for integration tests.

Before any destructive test setup, the fixture validates:

```text
POSTGRES_TEST_DB is configured
POSTGRES_TEST_DB != POSTGRES_DB
POSTGRES_TEST_DB ends with "_test"
```

If any condition fails, database tests fail closed.

The test database may be cleaned between tests because it contains only synthetic test data. The application database must not be truncated, deleted from, or otherwise reset by pytest.

`tests/test_database_fixture.py` also verifies the database identity with `SELECT current_database()`.

This separation is a safety boundary, not only a test convenience.

---

## Security Tests

Security tests remain deterministic and rule-oriented.

They verify behaviors such as:

- approved versus unauthorized models
- approved versus unauthorized destinations
- protected-data egress restrictions
- secret detection
- policy-bypass detection
- controlled exceptions
- runtime compromise state
- fail-closed behavior
- shutdown signaling and coordination
- tool authorization

Security tests should assert rule identifiers, allowed/blocked behavior, runtime state transitions, and sanitized outputs without inserting protected financial data into test logs.

---

## Test Data Safety

Real bank statements must never be used as committed fixtures.

PDF statements, extracted TXT files, CSV/OFX exports, database dumps, and other financial records remain protected even when they are used only for local parser development.

Local real-data validation may be performed outside tracked repository paths, but committed tests must use synthetic equivalents.

Before committing fixture changes:

```bash
git diff -- tests/fixtures/
git status
```

If real values were accidentally committed, removing them from the working tree is not sufficient. Repository history must be rewritten so that the exposed values are no longer present in reachable commits.

---

## Current Test Layers

The current test design can be summarized as:

```text
Security tests
    ↓
deterministic policy invariants

Parser fixture tests
    ↓
source-layout behavior

Parameterized parser tests
    ↓
classes of valid values

Normalization tests
    ↓
canonical-model invariants

Merchant normalization tests
    ↓
deterministic derived merchant

Transaction typing tests
    ↓
movement-type taxonomy

Expense categorization tests
    ↓
expense-purpose taxonomy and priority

Database fixture tests
    ↓
test-database isolation and fail-closed safety

PostgreSQL rule tests
    ↓
persistent aliases, categories, priorities, enabled state

Runtime financial pipeline tests
    ↓
production-oriented deterministic orchestration

Fingerprint tests
    ↓
identity relationships

Importer tests
    ↓
persistence and idempotency
```

At the current checkpoint, the complete suite passes:

```text
152 passed
```

Run the suite with:

```bash
pytest -q
```

or with verbose test names:

```bash
pytest -v
```

---

## Adding Tests for a New Bank Parser

When a new bank or source format is added:

1. Create a source-specific parser.
2. Create a fully synthetic structural fixture.
3. Test source-specific section boundaries and layout behavior.
4. Parameterize value formats that can vary.
5. Normalize parser output into the canonical model.
6. Verify normalization invariants.
7. Pass canonical transactions through generic merchant normalization, transaction typing, and expense categorization.
8. Reuse generic fingerprint and importer behavior.
9. Verify the complete test suite remains green.

The parser should contain source-specific knowledge.

The downstream canonical model, fingerprinting, importer, and financial tools should not require bank-specific logic unless their general contracts change.

---

## Rule of Thumb

Before adding a fixed expected value to a test, ask:

> Is this value itself the rule being tested, or is it merely one valid value present in a fixture?

If it is merely fixture data, test the property instead.

This keeps Sherlock Home's tests useful when synthetic fixtures evolve and prevents a passing test suite from depending on accidental sample values.

## Planned API Security Tests

The API will not be considered secure merely because endpoints return expected payloads.

Planned deterministic invariants:

```text
unauthenticated protected request → 401
authenticated but unauthorized request → 403
authenticated authorized request → permitted
invalid session → rejected
expired/revoked session → rejected
invalid CSRF token on mutating request → rejected
disabled user/session → rejected
login backoff/rate limit → enforced
public registration endpoint → absent
OpenAPI security scheme → present
```

Authentication and authorization tests must not invoke the LLM.

---
