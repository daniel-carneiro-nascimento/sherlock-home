# Financial Data Safety

## Core rule

Real financial statements and their extracted contents are protected data. They must remain inside the approved local environment and must not be committed to Git.

This rule applies equally to:

- original PDFs;
- CSV/OFX/QFX exports;
- text created by `pdftotext`;
- normalized statement files;
- debug dumps;
- database exports;
- screenshots containing financial information;
- prompts or logs containing statement contents.

## Where to keep real files

Prefer a location outside the repository or an explicitly ignored local data directory.

Example outside the repository:

```text
~/private-statement.pdf
~/private-statement.txt
```

If using a project data directory, verify that it is ignored before placing real data there.

## File permissions

On a single-user Linux development environment, local statement files can be restricted with:

```bash
chmod 600 ~/private-statement.pdf ~/private-statement.txt
```

This is an additional local filesystem control, not a replacement for encryption or host security.

## Git safety check

Before committing changes involving ingestion work:

```bash
git status
git diff --cached --name-only
```

Never assume that a file is safe merely because its extension is unusual.

## Extracted text is still sensitive

Running:

```bash
pdftotext -layout statement.pdf statement.txt
```

does not sanitize the document. The generated text usually contains the same protected financial information as the PDF and must be handled accordingly.

## LLM boundary

Real financial data may only be processed by explicitly approved local components under Sherlock Home's security policy. Secrets such as passwords, tokens, private keys, or database credentials must not be inserted into LLM context even when the model is local.

## Documentation and tests

Repository documentation should describe formats with synthetic examples. Tests should reproduce layout mechanics using fictional values and identifiers.


## Test database safety boundary

Automated persistence tests must never operate on the normal Sherlock Home application database.

The reference configuration separates:

```text
POSTGRES_DB=sherlock_home
POSTGRES_TEST_DB=sherlock_home_test
```

`tests/conftest.py` validates the test database before destructive setup and fails closed if:

- the test database is not configured
- the test database equals the application database
- the test database name does not end in `_test`

Only the disposable test database may be cleaned automatically between tests.

This protects locally imported financial records from accidental deletion during pytest execution.
