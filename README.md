# Sherlock Home

Sherlock Home is a local-first AI agent for personal finance analysis.

Current milestone: **v0.5.0 — deterministic financial ingestion and configurable local enrichment**.

Its purpose is to help users understand household spending, credit card usage, recurring expenses, cash flow, and financial behavior while keeping protected financial and personal data inside an explicitly approved local environment.

Sherlock Home is designed to be environment-agnostic.

You may run it on Linux, WSL, containers, bare metal, or another local setup, as long as the environment provides the required local services and does not violate the project security boundaries.

---

## Project Goals

Sherlock Home aims to provide a private AI-assisted environment for household financial analysis.

Planned capabilities include:

- Import bank and credit card statements
- Normalize financial transactions
- Categorize expenses
- Detect recurring expenses
- Analyze spending patterns
- Compare monthly financial behavior
- Track household cash flow
- Detect unusual spending
- Assist with budgeting
- Provide financial education based on actual user data
- Allow natural-language queries over local financial records

The main privacy principle is:

> Protected financial and personal data must not be processed by unapproved external services.

---

# Design Philosophy

Sherlock Home separates responsibilities between deterministic software and the LLM.

The central rule is:

> The LLM interprets financial information.  
> Deterministic software calculates financial information.  
> Security policy decides what is allowed to execute.

This separation is intentional.

It improves:

- reliability
- financial accuracy
- reproducibility
- auditability
- privacy
- security
- debuggability

---

# Architecture

Sherlock Home separates LLM reasoning from deterministic application behavior and security enforcement.

At a high level:

```text
User
  ↓
FastAPI
  ↓
Deterministic Security Enforcement
  ↓
Application Services / Approved Tools
  ↓
Local PostgreSQL and Approved Local AI Runtime
```

The LLM is not treated as a trusted security boundary. Parsing, financial calculations, authorization, persistence, and protected-operation decisions belong to deterministic application code.

For the complete architecture, including security boundaries, runtime flow, parser isolation, PostgreSQL, fingerprinting, idempotent imports, and future multi-bank design, see:

**[docs/architecture.md](docs/architecture.md)**

---

# Runtime Requirements

Sherlock Home is designed to run locally and does not require a specific operating system or virtualization platform.

A compatible environment should provide:

- Python
- an approved local LLM runtime
- local storage
- local database services when enabled
- sufficient CPU or GPU resources for the selected model
- local network access between approved components

Optional but recommended:

- GPU acceleration
- container support
- local PostgreSQL
- isolated runtime environments
- encrypted local storage

---

# Reference Development Environment

Sherlock Home is currently developed and tested using a local Linux-based environment with GPU-accelerated LLM inference.

This is only a reference environment, not a project requirement.

Users are free to deploy Sherlock Home using any local architecture that respects the project security model.

---

# Current AI Runtime

The current development implementation uses Ollama as a local model runtime.

Example configuration:

```env
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:14b
```

Currently approved development models may include:

```text
qwen3:14b
qwen3:4b
```

Model and destination allowlisting are enforced by deterministic application code.

---

# Local Project Context

Sherlock Home currently supports explicit local context injection from trusted project files such as:

```text
README.md
docs/architecture.md
```

The context loader is implemented in:

```text
app/services/project_context.py
```

This remains intentionally simple until the Local Retrieval phase.

---

# Security by Design

Sherlock Home uses deterministic security enforcement. The LLM may reason about a request, but it cannot authorize protected operations or override application policy.

Current controls include:

- approved-model validation
- approved local destination validation
- data-egress policy
- secret detection
- policy-bypass detection
- sanitized security audit events
- fail-closed runtime compromise state
- controlled shutdown handling
- tool authorization policy

Detailed security architecture and enforcement flow are documented in:

**[docs/architecture.md](docs/architecture.md#4-security-by-design)**

# Repository Structure

```text
sherlock-home/
├── alembic/
│   └── versions/
├── app/
│   ├── api/
│   ├── agents/
│   ├── core/
│   │   ├── audit.py
│   │   ├── config.py
│   │   ├── data_policy.py
│   │   ├── lifecycle.py
│   │   ├── network_policy.py
│   │   ├── policy_bypass.py
│   │   ├── runtime_state.py
│   │   ├── secret_detector.py
│   │   ├── security.py
│   │   ├── security_enforcer.py
│   │   ├── shutdown.py
│   │   ├── shutdown_coordinator.py
│   │   └── tool_policy.py
│   ├── db/
│   │   ├── base.py
│   │   └── database.py
│   ├── ingestion/
│   │   ├── expense_categorization.py
│   │   ├── fingerprint.py
│   │   ├── importer.py
│   │   ├── merchant_normalization.py
│   │   ├── normalization.py
│   │   ├── santander_pdf.py
│   │   └── transaction_typing.py
│   ├── models/
│   │   ├── category_rule.py
│   │   ├── merchant_alias.py
│   │   └── transaction.py
│   ├── rules/
│   │   ├── __init__.py
│   │   ├── categories.py
│   │   └── transaction_types.py
│   ├── services/
│   │   ├── category_rules.py
│   │   ├── financial_pipeline.py
│   │   ├── merchant_aliases.py
│   │   ├── ollama.py
│   │   └── project_context.py
│   ├── tools/
│   ├── __init__.py
│   └── main.py
├── data/
│   ├── inbox/
│   ├── processed/
│   └── samples/
├── docs/
│   ├── README.md
│   ├── architecture.md
│   ├── data-safety.md
│   ├── database.md
│   ├── financial-data-flow.md
│   ├── testing.md
│   └── parsers/
│       ├── README.md
│       └── santander.md
├── tests/
│   ├── fixtures/
│   ├── security/
│   ├── conftest.py
│   ├── test_category_rules.py
│   ├── test_category_rules_db.py
│   ├── test_database_fixture.py
│   ├── test_expense_categorization.py
│   ├── test_financial_pipeline.py
│   ├── test_fingerprint.py
│   ├── test_importer.py
│   ├── test_local_category_rules.py
│   ├── test_merchant_normalization.py
│   ├── test_normalization.py
│   ├── test_santander_pdf.py
│   ├── test_transaction_type_rules.py
│   └── test_transaction_typing.py
├── .env.example
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── LICENSE.md
├── pyproject.toml
└── README.md
```

---

# Current API

The current API is implemented using FastAPI.

The examples below use `jq` for readable JSON output.

Start the development server:

```bash
source .venv/bin/activate

uvicorn app.main:app --reload
```

Default address:

```text
http://127.0.0.1:8000
```

## Health Check

```bash
curl -s http://127.0.0.1:8000/health | jq
```

Expected response:

```json
{
  "status": "ok"
}
```

## Chat

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What are the architecture principles of Sherlock Home?"}'
```

Current request path:

```text
FastAPI
    ↓
Security Policy Validation
    ↓
Local Context
    ↓
Approved Local AI Runtime
    ↓
Approved LLM
    ↓
Response
```

---

# Security Test Example

To verify model enforcement, configure an unauthorized model:

```env
OLLAMA_MODEL=unauthorized-model
```

The request should be blocked before inference.

Expected audit event:

```json
{
  "event": "SECURITY_EVENT",
  "rule": "SH-AI-001",
  "severity": "critical",
  "action": "blocked",
  "reason": "unauthorized_ai_model"
}
```

The API should return a controlled security response such as:

```text
HTTP 403 Forbidden
```

No inference should occur.

---

# Data Handling

Real financial data must never be committed to Git.

Typical excluded data includes:

```text
data/inbox/
data/processed/
*.csv
*.ofx
*.qfx
*.xlsx
*.xls
*.pdf
*.db
*.sqlite
*.sqlite3
.env
```

Git is intended for:

- source code
- documentation
- architecture
- schemas
- tests
- synthetic examples

Git is not intended as storage for protected financial records.

Text extracted from a real bank PDF is still protected financial data. It must remain outside tracked repository paths or inside explicitly ignored local data directories. See `docs/data-safety.md`.

---

# Documentation

Detailed implementation and operating notes live under `docs/`:

- `docs/financial-data-flow.md` — implemented parser, normalization, merchant, transaction typing, categorization, fingerprint, and persistence pipeline
- `docs/database.md` — PostgreSQL, SQLAlchemy, Alembic, transaction schema, test-database isolation, and idempotency
- `docs/parsers/README.md` — parser architecture and bank-specific isolation
- `docs/parsers/santander.md` — Santander PDF parser behavior
- `docs/testing.md` — behavior-oriented testing, synthetic fixtures, parameterized inputs, and invariants
- `docs/data-safety.md` — rules for handling real statements and extracted text
- `docs/architecture.md` — broader project architecture

Bank-specific parsers are intentionally isolated. If one bank changes its statement layout, its parser can evolve without forcing unrelated bank parsers or the canonical transaction layer to change.

---

# Current Financial Data Flow

The first implemented end-to-end ingestion path handles Santander PDF statements with a usable text layer:

```text
Santander PDF
    ↓
pdftotext -layout
    ↓
Santander-specific deterministic parser
    ↓
ParsedStatement / ParsedTransaction
    ↓
statement normalization
    ↓
CanonicalStatement / CanonicalTransaction
    ↓
load active merchant aliases from PostgreSQL
    ↓
merchant normalization
    ↓
transaction typing
    ↓
load active category rules from PostgreSQL
    ↓
expense categorization
    ↓
SHA-256 fingerprint
    ↓
idempotent importer
    ↓
local PostgreSQL
```

The importer has been validated to skip previously imported transactions instead of duplicating them.

`transaction_type` and `category` represent different dimensions:

```text
transaction_type
    expense | income | transfer

category
    food | groceries | transport | utilities | health
    shopping | housing | financing | leisure | taxes | None
```

Only transactions typed as `expense` are eligible for expense categorization. `income` and `transfer` are movement types, not expense categories. Merchant, transaction type, and category are deterministic derived data and do not participate in the transaction fingerprint.

Bank-specific parsing is intentionally isolated so that changes in one bank's export format do not require changes to unrelated parsers or the canonical financial layer.

Detailed documentation:

- **[Architecture](docs/architecture.md)**
- **[Financial data flow](docs/financial-data-flow.md)**
- **[Database](docs/database.md)**
- **[Parser architecture](docs/parsers/README.md)**
- **[Santander parser](docs/parsers/santander.md)**
- **[Data safety](docs/data-safety.md)**
- **[Testing](docs/testing.md)**

---


## Runtime Financial Configuration

Starting with **v0.5.0**, user-editable financial enrichment rules are persisted locally in PostgreSQL rather than being treated as environment configuration.

Runtime configuration currently includes:

```text
merchant_aliases
category_rules
```

Both tables support deterministic priority ordering and enabled/disabled state.

The application runtime uses:

```text
app/services/financial_pipeline.py
```

to load active PostgreSQL rules and apply the enrichment sequence consistently.

`.env` remains for operational deployment configuration such as database connectivity, local AI endpoints, and runtime settings. It is not intended to be the future household-user configuration interface.

The planned web UI will manage local financial rules through the application API while PostgreSQL remains the persistent configuration source.

---

# Automated Tests

Security, ingestion, normalization, identity, and persistence behavior are covered by `pytest`.

Sherlock Home uses behavior-oriented tests rather than treating synthetic financial fixtures as golden records.

The testing model is:

```text
Structural fixture
    → validates source layout and parser behavior

Parameterized input
    → validates classes of valid values

Invariant tests
    → validate properties that must always hold
```

A fixture is therefore not treated as a golden financial record.

Examples:

- Santander fixtures validate layout, multiline descriptions, inherited dates, repeated headers, and section boundaries.
- Brazilian monetary parsing is tested with multiple parameterized synthetic values.
- Normalization tests verify invariants such as amount preservation, source metadata, and canonical description formatting.
- Fingerprint tests verify relationships such as same identity → same fingerprint and changed identity → different fingerprint.
- Importer tests derive the expected transaction count from the normalized statement rather than hard-coding fixture-specific counts.

Current coverage includes:

- approved and unauthorized AI models
- approved and unauthorized network endpoints
- financial data egress policy
- secret-data restrictions
- password and private-key detection
- policy-bypass detection
- system-prompt extraction attempts
- clean runtime state
- compromised runtime fail-closed behavior
- normal versus critical policy violations
- shutdown request state
- graceful shutdown coordinator integration
- tool authorization policy
- Santander statement structure parsing
- parameterized Brazilian monetary parsing
- multiline and inherited-date transaction behavior
- canonical statement normalization
- normalization invariants
- merchant normalization
- deterministic merchant aliases
- PostgreSQL-backed merchant alias loading
- deterministic merchant extraction and conservative unknown handling
- transaction-type taxonomy and deterministic typing
- expense-category taxonomy and explicit rule priorities
- optional local YAML category-rule loading
- PostgreSQL-backed configurable category rules
- runtime financial enrichment pipeline
- expense-only categorization
- transaction fingerprint invariants
- idempotent statement import
- persistence of derived merchant, category, and transaction type
- isolated PostgreSQL test database
- fail-closed guard preventing destructive tests from using the normal application database

Current validated suite:

```text
152 passed
```

Run the complete suite with:

```bash
pytest -q
```

For verbose test names:

```bash
pytest -v
```

Detailed testing methodology is documented in **[docs/testing.md](docs/testing.md)**.

Security controls and financial invariants should be accompanied by deterministic tests whenever practical.

---

# Roadmap

### v0.5.0 checkpoint

Phase 3 financial ingestion and deterministic enrichment is complete for the current Santander path.

```text
✓ deterministic Santander parsing
✓ canonical statement normalization
✓ merchant normalization
✓ merchant aliases
✓ transaction typing
✓ expense taxonomy
✓ expense categorization
✓ configurable local category rules
✓ PostgreSQL-backed runtime rules
✓ deterministic fingerprinting
✓ idempotent persistence
✓ isolated PostgreSQL integration testing
```



## Phase 1 — Local Runtime

- [x] Local LLM runtime
- [x] Local inference validated
- [x] Ollama integration
- [x] Qwen3 integration
- [x] FastAPI
- [x] Local project context
- [x] Deterministic security enforcement

## Phase 2 — Security

- [x] Approved model validation
- [x] Approved local destination validation
- [x] Sanitized security event logging
- [x] Controlled policy exceptions
- [x] Data egress protection
- [x] Secret detection
- [x] Policy bypass detection
- [x] Automated security tests
- [x] Runtime compromise state
- [x] Fail-closed behavior after critical violations
- [x] Controlled shutdown request state
- [x] FastAPI/Uvicorn graceful shutdown lifecycle integration
- [x] Tool authorization policy

## Phase 3 — Financial Data

- [x] PostgreSQL local database
- [x] SQLAlchemy integration
- [x] Alembic migrations
- [x] Transaction schema
- [x] Santander PDF statement ingestion
- [x] Transaction fingerprinting
- [x] Idempotent statement import
- [ ] CSV ingestion
- [ ] OFX ingestion
- [x] Statement normalization
- [x] Transaction typing
- [x] Category taxonomy and deterministic rule priority
- [x] Merchant normalization
- [x] Expense categorization

## Phase 4 — Financial Tools

- [ ] Monthly spending
- [ ] Category spending
- [ ] Recurring expenses
- [ ] Cash-flow analysis
- [ ] Spending comparison
- [ ] Anomaly detection

## Phase 5 — Agentic Layer

- [ ] Tool dispatcher
- [ ] Deterministic tool execution
- [ ] Structured tool responses
- [ ] Agent reasoning
- [ ] Financial workflows
- [ ] Tool permission boundaries

## Phase 6 — Local Retrieval

- [ ] Local embeddings
- [ ] Local vector storage
- [ ] Financial document retrieval
- [ ] Selective context injection
- [ ] Retrieval security controls

## Phase 7 — User Interface

- [ ] Local dashboard
- [ ] Financial charts
- [ ] Natural-language query interface
- [ ] Monthly reports
- [ ] Alerts
- [ ] Financial insights

---

# Development Principle

Sherlock Home should remain portable.

Environment-specific setup should not become a hard architectural requirement unless technically necessary.

The intended workflow is:

```text
git clone
    ↓
choose a local runtime
    ↓
configure an approved local model
    ↓
configure local services
    ↓
run Sherlock Home
```

The project should prefer explicit configuration over assumptions about the user's operating system, GPU, virtualization platform, or deployment method.

---

# License

Sherlock Home is licensed under the **GNU General Public License v3.0 or later (GPL-3.0-or-later)**.

You are free to use, study, modify, and redistribute this software under the terms of the GPLv3.

Distributed derivative works must preserve the freedoms granted by the GPL and provide the corresponding source code under GPL-compatible terms.

See `LICENSE.md` for the complete license text.
