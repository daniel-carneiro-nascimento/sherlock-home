# Financial Data Flow

## Current implemented path

The implemented financial ingestion path begins with a Santander bank statement exported as a PDF containing a usable text layer.

```mermaid
flowchart TD
    PDF[Bank PDF - local only]
    PDF --> TEXT[pdftotext -layout]
    TEXT --> PARSER[Santander-specific parser]
    PARSER --> PARSED[ParsedStatement / ParsedTransaction]
    PARSED --> CHECK[Parser sanity checks]
    CHECK --> NORMALIZE[Statement normalization]
    NORMALIZE --> CANON[CanonicalStatement / CanonicalTransaction]
    CANON --> MALIAS[(PostgreSQL merchant aliases)]
    MALIAS --> MERCHANT[Merchant normalization]
    MERCHANT --> TYPE[Transaction typing]
    TYPE --> CRULES[(PostgreSQL category rules)]
    CRULES --> CATEGORY[Expense categorization]
    CATEGORY --> FP[Transaction fingerprint]
    FP --> IMPORT[Idempotent importer]
    IMPORT --> DB[(Local PostgreSQL)]
```

No external AI service participates in this ingestion path.

## Separation of responsibilities

### PDF/text extraction

External tooling such as Poppler `pdftotext -layout` converts a local PDF into local text. It does not decide what constitutes a financial transaction.

### Bank parser

The bank parser understands Santander statement layout. It locates statement metadata, identifies the movement section, parses monetary values, handles multiline descriptions and inherited dates, and rejects suspicious structures.

Bank-specific layout knowledge must terminate at this boundary.

### Statement normalization

`app/ingestion/normalization.py` converts source-specific parsed objects into the canonical financial model.

Normalization may canonicalize representation, such as description whitespace and source metadata, but must not silently alter financial meaning.

### Merchant normalization

`app/ingestion/merchant_normalization.py` derives a normalized merchant only when deterministic patterns recognize one.

Unknown patterns remain `None`. The LLM is not used to guess merchant identity.

### Transaction typing

`app/ingestion/transaction_typing.py` determines the nature of the financial movement.

Current transaction types are:

```text
expense
income
transfer
```

Explicit rules are evaluated first. The fallback uses the amount sign for ordinary income/expense classification.

### Expense categorization

`app/ingestion/expense_categorization.py` categorizes only transactions already typed as `expense`.

The taxonomy and rule priorities live separately under `app/rules/categories.py`.

Current expense categories are:

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

`income` and `transfer` are not expense categories and therefore keep `category=None`.

### Fingerprint and importer

The importer creates deterministic fingerprints and checks the database before insertion. Re-importing the same statement must not create duplicate transactions.

Merchant, transaction type, and category are derived enrichment fields and do not participate in the fingerprint.

### PostgreSQL

The local database is the source for deterministic financial calculations. The LLM does not need database credentials and should not perform financial arithmetic from raw statement text.

## Current semantic model

```text
CanonicalTransaction
├── source identity
│   ├── transaction_date
│   ├── amount
│   ├── original_description
│   ├── document
│   ├── statement_month
│   ├── source
│   ├── source_type
│   └── source_account
│
└── deterministic enrichment
    ├── merchant
    ├── transaction_type
    └── category
```

The source identity participates in fingerprint generation. Derived enrichment does not.

## Runtime enrichment service

The current runtime path centralizes enrichment in:

```text
app/services/financial_pipeline.py
```

The service exposes a single deterministic orchestration boundary for canonical statements.

```text
ParsedStatement
    ↓
normalize_santander_statement()
    ↓
load_merchant_aliases_from_db()
    ↓
normalize_statement_merchants()
    ↓
classify_statement_transactions()
    ↓
load_category_rules_from_db()
    ↓
categorize_statement_expenses()
    ↓
CanonicalStatement ready for fingerprint/import
```

This prevents individual callers from needing to manually assemble runtime rule inputs.

### Merchant aliases

Active merchant aliases are loaded from PostgreSQL in priority order.

Unmatched merchants remain unchanged; the application does not invent an alias.

### Category rules

Default deterministic rules remain available in code.

Enabled PostgreSQL category rules are merged into the active rule set and ordered by explicit priority. A lower-priority-number local rule can intentionally override a broader default rule.

Disabled database rules are ignored.

### Optional YAML rules

Local YAML category-rule loading remains supported as a deterministic import/bootstrap mechanism. It is not the intended interactive runtime configuration interface.

The local web UI can manage PostgreSQL-backed rules through authenticated API endpoints.

## Analysis boundary

With canonical transactions persisted, Phase 5 now provides the deterministic analysis layer:

```text
Local PostgreSQL
    ↓
app/services/financial_analysis.py
    ↓
monthly spending
category spending
spending comparison
recurring expenses
cash-flow analysis
anomaly detection
    ↓
structured deterministic results
    ↓
authenticated application / approved tool boundary
    ↓
Phase 6 agent orchestration
    ↓
LLM interpretation / explanation
```

Financial tools query persisted canonical data. They do not re-parse statements and do not ask the LLM to calculate totals.

Phase 5 is complete and validated as part of the `234 passed` project baseline.

Phase 6 must consume these deterministic primitives through an approved tool registry/dispatcher rather than exposing arbitrary SQL or duplicating financial arithmetic in the LLM.

See [`financial-tools.md`](financial-tools.md).

## Future multi-bank flow

```mermaid
flowchart LR
    A[Santander PDF] --> AP[Santander Parser]
    B[Bank B CSV] --> BP[Bank B Parser]
    C[Bank C OFX] --> CP[Bank C Parser]
    D[Bank D PDF] --> DP[Bank D Parser]

    AP --> NORM[Canonical normalization]
    BP --> NORM
    CP --> NORM
    DP --> NORM

    NORM --> ENRICH[Generic deterministic enrichment]
    ENRICH --> DB[(PostgreSQL)]
    DB --> TOOLS[Deterministic Financial Tools]
```

The parser boundary is deliberate. If one bank changes its export format, the expected change surface is that bank's parser plus its synthetic fixtures and parser tests. Merchant normalization, transaction typing, categorization, fingerprinting, persistence, and financial tools remain generic downstream stages.

## API boundary

The financial pipeline and financial tools remain independent of API authentication.

```text
authenticated API request
    ↓
authorized application service/tool
    ↓
deterministic financial query
```

Authentication logic must not move into parsers, merchant normalization, transaction typing, categorization, fingerprinting, persistence, or financial arithmetic.
