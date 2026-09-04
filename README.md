<p align="center">
  <img src="docs/assets/sherlock-home_banner.png" alt="Sherlock Home banner" width="100%">
</p>

Sherlock Home is a **local-first AI agent for personal finance analysis**.

It is designed to help a household understand spending, credit card usage, recurring expenses, cash flow, and financial behavior while keeping protected financial and personal data inside explicitly approved local infrastructure.

> **Privacy principle:** protected financial and personal data must not be processed by unapproved external services.

## Why Sherlock Home

Sherlock Home separates deterministic application logic from LLM reasoning:

> **The LLM interprets financial information.**  
> **Deterministic software calculates financial information.**  
> **Security policy decides what is allowed to execute.**

The LLM is never treated as a trusted security boundary.

Current design priorities:

- local-first processing;
- deterministic financial calculations;
- explicit model and destination allowlists;
- protected-data egress controls;
- local PostgreSQL persistence;
- authenticated, CSRF-protected API access;
- auditable protected configuration changes;
- portable deployment across Linux, WSL, containers, bare metal, or equivalent private environments.

## Current Status

The project currently includes:

- local Ollama/Qwen3 integration;
- deterministic security enforcement and fail-closed runtime controls;
- PostgreSQL + SQLAlchemy + Alembic;
- deterministic Santander PDF ingestion;
- transaction fingerprinting and idempotent imports;
- canonical transaction normalization;
- deterministic merchant normalization and PostgreSQL-backed merchant aliases;
- transaction typing;
- deterministic expense categorization and PostgreSQL-backed category rules;
- runtime financial enrichment orchestration;
- isolated PostgreSQL integration testing;
- authenticated `/api/v1` API;
- Argon2id password hashing;
- server-side sessions with secure `__Host-` cookies;
- CSRF protection;
- login throttling/backoff;
- session TTL, idle timeout, revocation, logout-all, and password rotation;
- opaque public resource identifiers;
- persistent protected-configuration audit events;
- private HTTPS development/deployment model;
- deterministic Phase 5 financial-analysis services;
- monthly and category spending analysis;
- month-to-month spending comparison;
- deterministic recurring-expense detection;
- deterministic cash-flow analysis;
- deterministic anomaly detection;
- **327 automated tests passing**.

The detailed project plan lives outside this README:

**[View the Roadmap](docs/ROADMAP.md)**

[![Sherlock Home Roadmap](docs/assets/roadmap.svg)](docs/ROADMAP.md)

## Architecture

```text
User / Household UI
        ↓
Private HTTPS
        ↓
Authenticated FastAPI /api/v1
        ↓
Deterministic Security Enforcement
        ↓
Application Services / Approved Tools
        ↓
Local PostgreSQL + Approved Local AI Runtime
```

Parsing, financial calculations, authorization, persistence, CSRF enforcement, session handling, and protected-operation decisions belong to deterministic application code.

For the complete architecture:

- **[Backend Architecture](docs/architecture.md)** — application services, security boundaries, API, persistence, ingestion, deterministic tools, and local AI runtime
- **[Frontend Architecture](docs/frontend/architecture.md)** — web shell, navigation, view-model boundary, themes, accessibility, household goals, and chat UX

## Current AI Runtime

The reference development implementation uses Ollama:

```env
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:14b
```

Approved local models are controlled by deterministic allowlisting.

The runtime is intentionally environment-agnostic. A compatible deployment may use Linux, WSL, containers, bare metal, or another private architecture that respects Sherlock Home's security boundaries.

### Ollama prerequisite

Sherlock Home expects an approved Ollama runtime to already be installed and running.

Ollama is **not installed or started automatically by Sherlock Home**. Before starting the application, install Ollama using the official instructions for your operating system and make sure the configured model is available locally.

For the reference configuration:

```bash
ollama pull qwen3:14b
ollama list
```

Configure Sherlock Home through `.env`:

```env
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:14b
```

Verify that the local Ollama runtime is reachable before starting Sherlock Home:

```bash
curl http://127.0.0.1:11434/api/tags
```

If Ollama is running on another approved local or private endpoint, update `OLLAMA_HOST` accordingly.

The expected startup flow is:

```text
Install Ollama
    ↓
Start Ollama
    ↓
Pull an approved model
    ↓
Configure OLLAMA_HOST and OLLAMA_MODEL
    ↓
Verify the Ollama endpoint
    ↓
Start Sherlock Home
```

> Protected household and financial data must only be sent to an approved local/private Ollama endpoint. Do not configure a public or third-party inference endpoint for protected Sherlock Home data.

## Authenticated API

The protected API is versioned under:

```text
/api/v1
```

Current authentication/security behavior includes:

- single-household user model;
- no public registration;
- local admin bootstrap;
- Argon2id password hashing;
- server-side sessions;
- `Secure`, `HttpOnly`, `SameSite=Strict` session cookies;
- `__Host-` cookie semantics;
- CSRF protection on state-changing requests;
- source-aware login throttling and backoff;
- authorization dependencies;
- OpenAPI cookie security scheme;
- session expiration and idle timeout;
- logout, logout-all, and password change with session revocation.

Development HTTPS:

```bash
python -m scripts.run_https
```

Reference local endpoint:

```text
https://127.0.0.1:8443
```

API details:

- **[API v1 contract](docs/API_V1.md)**
- **[Private HTTPS deployment](docs/PRIVATE_HTTPS_DEPLOYMENT.md)**

## Financial Data Pipeline

The first implemented bank-specific ingestion path uses Santander PDF statements with a usable text layer:

```text
Santander PDF
    ↓
pdftotext -layout
    ↓
Santander-specific deterministic parser
    ↓
ParsedStatement / ParsedTransaction
    ↓
parser sanity checks
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

No external AI service participates in this ingestion path.

`merchant`, `transaction_type`, and `category` are deterministic derived enrichment fields. They are persisted for later analysis but are intentionally excluded from transaction fingerprint identity.

Bank-specific parsers are isolated so one bank's format can evolve without forcing unrelated parsers or the canonical financial layer to change.

The runtime orchestration boundary is documented in **[docs/financial-data-flow.md](docs/financial-data-flow.md)**.

## Security by Design

Current deterministic controls include:

- approved-model validation;
- approved local destination validation;
- financial-data egress policy;
- secret detection;
- policy-bypass detection;
- sanitized security events;
- runtime compromise state;
- fail-closed behavior after critical violations;
- controlled shutdown handling;
- tool authorization policy;
- authenticated API authorization;
- CSRF enforcement;
- login rate limiting/backoff;
- persistent protected-configuration audit events.

Financial data must not be sent to external LLM, embedding, telemetry, analytics, advertising, profiling, training, or evaluation services.

## Data Handling

Real financial data must never be committed to Git.

Typical protected/local-only data includes:

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

Git is intended for source code, documentation, architecture, schemas, tests, and synthetic examples.

See **[docs/data-safety.md](docs/data-safety.md)**.

## Testing

Run the full suite with:

```bash
pytest -q
```

Current validated baseline:

```text
234 passed
```

Coverage includes security policy, ingestion, persistence, authentication, authorization, CSRF, session lifecycle, rate limiting, opaque IDs, API contract checks, protected configuration audit behavior, deterministic financial enrichment, and the complete Phase 5 financial-analysis service layer.

See **[docs/testing.md](docs/testing.md)**.

## Current Development Frontier

**Phase 5 — Financial Tools is complete.**

The implemented deterministic service layer provides:

```text
get_monthly_spending()
get_category_spending()
compare_monthly_spending()
find_recurring_expenses()
get_cash_flow()
detect_spending_anomalies()
```

The next major functional phase is **Phase 6 — Agentic Layer**.

The first Phase 6 boundary is:

```text
agent request
    ↓
approved tool registry / dispatcher
    ↓
deterministic tool authorization
    ↓
existing financial-analysis service
    ↓
structured result
    ↓
LLM interpretation / explanation
```

CSV and OFX ingestion remain open Phase 3 adapters, but they do not block Phase 6 because the canonical Santander pipeline already persists normalized, typed, categorized transactions.

See:

- **[Roadmap](docs/ROADMAP.md)**
- **[Financial tools](docs/financial-tools.md)**

## Documentation

Detailed documentation lives under `docs/`:

- **[Backend Roadmap](docs/ROADMAP.md)** — backend/application phases, status, and implementation milestones
- **[Frontend Roadmap](docs/frontend/ROADMAP.md)** — household-facing web phases and Holmes-Hat minimum UI
- **[Backend Architecture](docs/architecture.md)** — application services, security boundaries, API, persistence, ingestion, deterministic tools, and local AI runtime
- **[Frontend Architecture](docs/frontend/architecture.md)** — web shell, navigation, view-model boundary, themes, accessibility, household goals, and chat UX
- **[API v1](docs/API_V1.md)** — authenticated API contract
- **[Private HTTPS deployment](docs/PRIVATE_HTTPS_DEPLOYMENT.md)** — private deployment model
- **[Financial data flow](docs/financial-data-flow.md)** — ingestion and deterministic enrichment pipeline
- **[Financial tools](docs/financial-tools.md)** — implemented deterministic analysis services and Phase 6 integration boundary
- **[Database](docs/database.md)** — PostgreSQL, SQLAlchemy, Alembic, and idempotency
- **[Parser architecture](docs/parsers/README.md)** — parser isolation strategy
- **[Santander parser](docs/parsers/santander.md)** — current bank-specific parser
- **[Data safety](docs/data-safety.md)** — protected-data handling
- **[Testing](docs/testing.md)** — deterministic and synthetic test strategy
