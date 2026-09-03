<p align="center">
  <img src="docs/assets/sherlock-home_banner.png" alt="Sherlock Home banner" width="100%">
</p>
# Sherlock Home

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
- transaction normalization, typing, merchant normalization, and expense categorization;
- runtime category rules and merchant aliases;
- authenticated `/api/v1` API;
- Argon2id password hashing;
- server-side sessions with secure `__Host-` cookies;
- CSRF protection;
- login throttling/backoff;
- session TTL, idle timeout, revocation, logout-all, and password rotation;
- opaque public resource identifiers;
- persistent protected-configuration audit events;
- private HTTPS development/deployment model;
- **195 automated tests passing**.

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

**[docs/architecture.md](docs/architecture.md)**

## Current AI Runtime

The reference development implementation uses Ollama:

```env
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:14b
```

Approved local models are controlled by deterministic allowlisting.

The runtime is intentionally environment-agnostic. A compatible deployment may use Linux, WSL, containers, bare metal, or another private architecture that respects Sherlock Home's security boundaries.

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
normalization + validation
    ↓
SHA-256 fingerprint
    ↓
idempotent importer
    ↓
local PostgreSQL
```

Bank-specific parsers are intentionally isolated so one bank's format can evolve without forcing unrelated parsers or the canonical transaction layer to change.

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
195 passed
```

Coverage includes security policy, ingestion, persistence, authentication, authorization, CSRF, session lifecycle, rate limiting, opaque IDs, API contract checks, and protected configuration audit behavior.

See **[docs/testing.md](docs/testing.md)**.

## Documentation

Detailed documentation lives under `docs/`:

- **[Roadmap](docs/ROADMAP.md)** — project phases, status, and next milestones
- **[Architecture](docs/architecture.md)** — security boundaries and system design
- **[API v1](docs/API_V1.md)** — authenticated API contract
- **[Private HTTPS deployment](docs/PRIVATE_HTTPS_DEPLOYMENT.md)** — private deployment model
- **[Financial data flow](docs/financial-data-flow.md)** — ingestion pipeline
- **[Database](docs/database.md)** — PostgreSQL, SQLAlchemy, Alembic, and idempotency
- **[Parser architecture](docs/parsers/README.md)** — parser isolation strategy
- **[Santander parser](docs/parsers/santander.md)** — current bank-specific parser
- **[Data safety](docs/data-safety.md)** — protected-data handling
- **[Testing](docs/testing.md)** — deterministic and synthetic test strategy

## Development Principle

Sherlock Home should remain portable.

```text
git clone
    ↓
choose a private/local runtime
    ↓
configure an approved local model
    ↓
configure local services
    ↓
run Sherlock Home
```

Environment-specific setup should not become a hard architectural requirement unless technically necessary.

## License

Sherlock Home is licensed under the **GNU General Public License v3.0 or later (`GPL-3.0-or-later`)**.

See [`LICENSE.md`](LICENSE.md) for the complete license text.
