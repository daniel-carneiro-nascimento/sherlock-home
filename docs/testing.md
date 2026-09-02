# Testing Financial Ingestion

## Rule: test layout, not real finances

Tests must use synthetic data that reproduces the structure of a real bank export without reproducing real financial records.

A synthetic fixture should preserve the properties the parser depends on:

- headings;
- column order;
- spacing when relevant;
- date format;
- decimal/thousands separators;
- debit/credit sign convention;
- optional document fields;
- multiline-description behavior;
- page-header repetition when relevant;
- section boundary markers.

Names, identifiers, amounts, balances, merchants, and descriptions must be invented.

## Creating a fixture safely

1. Inspect the real statement locally.
2. Identify only its structural patterns.
3. Create a new text file from scratch under `tests/fixtures/`.
4. Use fictional merchants, fictional document numbers, and fictional amounts.
5. Preserve the mathematical/format behavior needed by the parser.
6. Review the fixture before `git add` to ensure no copied personal identifiers or real transaction descriptions remain.

Do not sanitize a real statement by merely deleting a few names and then commit the result. A fixture should be intentionally synthetic.

## Santander fixture

The Santander fixture should include cases for:

- statement month header;
- standard debit;
- standard credit where useful;
- trailing minus notation;
- transaction with document number;
- transaction without document number;
- transaction without a repeated date;
- multiline description;
- movement-section end marker.

## Tests

Current financial-data tests cover parsing, Brazilian monetary conversion, fingerprint stability, and idempotent import.

Run the full suite:

```bash
pytest -q
```

The currently validated project suite at this checkpoint is:

```text
35 passed
```

## Real-file validation

A real local statement may be used for manual/integration validation, but tests should print only structural metrics when possible, such as:

```text
statement month
transaction count
positive/negative count
missing optional field count
description length range
```

Avoid printing transaction descriptions, account identifiers, document identifiers, or balances into logs merely to prove the parser works.
