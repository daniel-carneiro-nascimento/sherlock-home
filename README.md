# Sherlock Home

Sherlock Home is a local-first AI agent for personal finance analysis.

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

# High-Level Architecture

```mermaid
flowchart TD

    USER[User]

    USER --> API[FastAPI]

    API --> SEC[Deterministic Security Enforcement Layer]

    SEC -->|Allowed| CTX[Local Context / Tool Layer]
    SEC -->|Blocked| AUDIT[Sanitized Security Audit]

    CTX --> AGENT[Sherlock Home Agent]

    AGENT --> LOCALAI[Approved Local AI Runtime]

    LOCALAI --> LLM[Approved Local LLM]

    LLM --> AGENT

    AGENT --> API

    API --> USER
```

The LLM is not treated as a trusted security boundary.

Security decisions are made by deterministic application code before protected operations are executed.

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

This is only a reference environment.

It is not a project requirement.

Users are free to deploy Sherlock Home using any local architecture that respects the project security model.

Deployment-specific documentation should remain separate from application architecture whenever possible.

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

The allowed model list is enforced by application code.

The project should not assume that a model is trusted simply because it is installed locally.

Only explicitly approved models may process protected user data.

---

# Current Request Flow

```mermaid
sequenceDiagram

    participant User
    participant FastAPI
    participant Security
    participant Context
    participant Ollama
    participant LLM

    User->>FastAPI: POST /chat

    FastAPI->>Security: Validate model and destination

    alt Security policy violation
        Security->>Security: Block operation
        Security->>FastAPI: Raise controlled security exception
        Security->>Security: Emit sanitized audit event
        FastAPI-->>User: Controlled HTTP response
    else Allowed
        Security->>Context: Continue
        Context->>Context: Load trusted local context
        Context->>Ollama: System prompt + context + user input
        Ollama->>LLM: Local inference
        LLM-->>Ollama: Response
        Ollama-->>FastAPI: Response
        FastAPI-->>User: JSON response
    end
```

---

# Local Project Context

Sherlock Home currently supports explicit local context injection.

Examples of trusted project context may include:

```text
README.md
docs/architecture.md
```

The context loader is implemented in:

```text
app/services/project_context.py
```

This is intentionally simple.

At this stage, Sherlock Home does not need a full vector database or RAG subsystem to answer questions about a small number of local project files.

As the project grows, this can later evolve into:

- local embeddings
- semantic retrieval
- vector search
- document chunking
- selective context loading

Protected financial data must still follow the same security rules regardless of retrieval method.

---

# Deterministic Security Enforcement Layer

Sherlock Home includes a deterministic security layer implemented directly in application code.

This is a core architectural feature.

The security model does not rely on the LLM to decide whether an operation is safe.

The LLM may receive instructions describing security policy, but the actual enforcement must occur in deterministic code.

```mermaid
flowchart TD

    INPUT[Incoming Request]

    INPUT --> POLICY[Security Policy Validation]

    POLICY --> MODEL{Approved Model?}

    MODEL -->|No| AIBLOCK[Block SH-AI-001]
    MODEL -->|Yes| HOST{Approved Destination?}

    HOST -->|No| NETBLOCK[Block SH-NET-001]
    HOST -->|Yes| EXEC[Allow Operation]

    AIBLOCK --> AUDIT[Sanitized Security Audit]
    NETBLOCK --> AUDIT

    AUDIT --> ERROR[Controlled Security Response]

    EXEC --> SERVICE[Approved Local Service]
```

This layer is deterministic because:

- rules are encoded in Python
- rules can be unit tested
- decisions do not depend on model reasoning
- violations produce predictable results
- protected operations are blocked before execution
- audit output can be inspected independently of the model

---

# Security Components

The current security architecture is organized around:

```text
app/core/security.py
app/core/security_enforcer.py
app/core/audit.py
```

## `security.py`

Defines security policies and validation rules.

Typical responsibilities include:

- approved AI models
- approved hosts
- approved local services
- security rule identifiers
- severity levels
- shutdown requirements

Example concept:

```python
APPROVED_MODELS = {
    "qwen3:14b",
    "qwen3:4b",
}
```

If a configured model is not explicitly approved, it is rejected before inference.

## `security_enforcer.py`

Executes policy decisions.

Typical responsibilities:

- reject unauthorized operations
- stop execution before protected actions occur
- raise controlled security exceptions
- determine whether execution may continue
- escalate critical violations

Security enforcement must not depend on natural-language interpretation by the LLM.

## `audit.py`

Produces sanitized security events.

The audit layer should record security events without leaking protected information.

Security logs must not contain:

- full prompts
- financial transactions
- account numbers
- card numbers
- passwords
- API keys
- tokens
- credentials
- document contents
- sensitive personal information

Example:

```json
{
  "timestamp": "2026-09-01T21:19:13+00:00",
  "event": "SECURITY_EVENT",
  "rule": "SH-AI-001",
  "severity": "critical",
  "action": "blocked",
  "reason": "unauthorized_ai_model"
}
```

The purpose of the audit event is to record:

- which rule was triggered
- what class of security event occurred
- whether it was blocked
- how severe it was

The purpose is not to log the sensitive content that caused the event.

---

# Security Policy Rules

Security controls use explicit identifiers.

Current and planned rules include:

| Rule | Description |
|---|---|
| `SH-AI-001` | Unauthorized AI model |
| `SH-NET-001` | Unauthorized network destination |
| `SH-DATA-001` | Unauthorized external transmission of protected data |
| `SH-SECRET-001` | Secret or credential exposure |
| `SH-POLICY-001` | Attempt to bypass or override security policy |

Additional rules may be added as the project evolves.

---

# Security Enforcement Flow

```mermaid
flowchart LR

    INPUT[Input / Request]

    INPUT --> VALIDATE[Policy Validation]

    VALIDATE --> DECISION{Allowed?}

    DECISION -->|Yes| EXECUTE[Execute Approved Local Operation]

    DECISION -->|No| BLOCK[Block Operation]

    BLOCK --> LOG[Sanitized Security Event]

    LOG --> CRITICAL{Critical Security Boundary Violation?}

    CRITICAL -->|No| CONTINUE[Application Continues]

    CRITICAL -->|Yes| ABORT[Abort Operation]

    ABORT --> SAFE{Containment Guaranteed?}

    SAFE -->|Yes| CONTINUE

    SAFE -->|No| SHUTDOWN[Clean Shutdown]
```

A normal policy violation should not automatically terminate the application.

Otherwise, an attacker could deliberately trigger a rule repeatedly and use the security layer as a denial-of-service mechanism.

A clean shutdown should be reserved for cases where continuing execution may no longer be safe.

Examples:

- protected data may leave the approved environment
- unauthorized external processing may occur
- credentials may be exposed
- containment cannot be guaranteed
- the trusted execution boundary appears compromised

---

# Security Principles

Core principles:

- Protected financial data must remain inside approved local components.
- Do not invent balances, transactions, debts, income, or financial facts.
- Financial calculations should be performed by deterministic tools, application logic, or database queries whenever possible.
- The LLM is responsible for interpretation, reasoning, orchestration, and explanation.
- Clearly distinguish facts from assumptions.
- Prefer actual local financial records over generic advice.
- Do not expose secrets, credentials, account numbers, card numbers, or sensitive identifiers.
- Do not claim to be a bank, broker, accountant, tax professional, or licensed financial adviser.
- Financial guidance should be presented as analytical or educational assistance.
- Security enforcement must not depend exclusively on model behavior.

---

# Project Knowledge Rules

When answering questions about Sherlock Home:

- Use the provided local project context as the primary source of truth.
- Do not claim that a feature exists unless it is documented or implemented.
- If something is a design inference or recommendation, state that clearly.
- If project context is insufficient, say so.
- Project documentation may be processed by approved local models.
- Protected financial and personal data may only be processed by approved local components.
- Secrets and credentials should never be inserted into LLM context.

---

# Forbidden Operations

The following operations are prohibited:

- Send protected user financial or personal data to an external LLM.
- Send protected data to a cloud API.
- Use an AI model that has not been explicitly approved.
- Use internet-accessible services to process protected financial or personal data.
- Send transaction data, documents, embeddings, metadata, prompts, or derived financial information outside the approved environment.
- Automatically enable telemetry, remote inference, cloud processing, or external AI integrations.
- Pass passwords, credentials, tokens, account numbers, card numbers, or other secrets into LLM context.
- Attempt to disable, override, bypass, or circumvent security policy.

A service must not be considered trusted simply because it is accessed through:

- `localhost`
- a container
- an SDK
- a Python package
- a plugin
- an API abstraction
- a local proxy

Trust must be explicit.

---

# Security Boundary

```mermaid
flowchart TB

    subgraph TRUSTED["Approved Local Environment"]

        API[FastAPI]

        POLICY[Deterministic Security Enforcement]

        DB[(Local Database)]

        TOOLS[Deterministic Tools]

        LOCALAI[Approved Local AI Runtime]

        LLM[Approved Local LLM]

        API --> POLICY
        POLICY --> TOOLS
        POLICY --> DB
        POLICY --> LOCALAI
        LOCALAI --> LLM

    end

    subgraph UNTRUSTED["External / Unapproved Environment"]

        CLOUD[Cloud Services]
        EXTLLM[External AI Models]
        EXTAPI[External APIs]
        INTERNET[Internet Services]

    end

    POLICY -. BLOCK .-> CLOUD
    POLICY -. BLOCK .-> EXTLLM
    POLICY -. BLOCK .-> EXTAPI
    POLICY -. BLOCK .-> INTERNET
```

The security boundary is defined by explicit approval.

It is not defined only by physical location or network address.

---

# Repository Structure

```text
sherlock-home/
├── app/
│   ├── api/
│   ├── agents/
│   ├── core/
│   │   ├── audit.py
│   │   ├── config.py
│   │   ├── security.py
│   │   └── security_enforcer.py
│   ├── db/
│   ├── ingestion/
│   ├── models/
│   ├── services/
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
│   └── architecture.md
├── infra/
├── logs/
├── scripts/
├── tests/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

---

# Current API

The current API is implemented using FastAPI.

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
curl http://127.0.0.1:8000/health
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

---

# Planned Financial Architecture

```mermaid
flowchart TD

    FILES[Bank / Credit Card Statements]

    FILES --> INGEST[Local Ingestion]

    INGEST --> NORMALIZE[Transaction Normalization]

    NORMALIZE --> DB[(Local Database)]

    DB --> TOOLS[Deterministic Financial Tools]

    TOOLS --> POLICY[Security Policy]

    POLICY --> AGENT[Sherlock Home Agent]

    AGENT --> LLM[Approved Local LLM]

    LLM --> AGENT

    AGENT --> API[FastAPI]

    API --> UI[Local UI]
```

Potential deterministic tools include:

```text
get_monthly_spending()

get_credit_card_statement()

get_category_total()

compare_months()

find_recurring_expenses()

forecast_cash_flow()

detect_spending_anomalies()
```

The LLM should orchestrate these tools rather than calculate financial values itself.

---

# Future Agentic Flow

```mermaid
sequenceDiagram

    participant User
    participant Agent
    participant Policy
    participant Tool
    participant DB
    participant LLM

    User->>Agent: Can I afford a R$ 4,000 purchase?

    Agent->>Policy: Request tool execution

    Policy-->>Agent: Allowed

    Agent->>Tool: get_cash_balance()
    Tool->>DB: Query
    DB-->>Tool: Result
    Tool-->>Agent: Balance

    Agent->>Tool: get_upcoming_bills()
    Tool->>DB: Query
    DB-->>Tool: Result
    Tool-->>Agent: Upcoming obligations

    Agent->>Tool: get_emergency_reserve()
    Tool->>DB: Query
    DB-->>Tool: Result
    Tool-->>Agent: Reserve

    Agent->>LLM: Interpret deterministic results

    LLM-->>Agent: Explanation

    Agent-->>User: Financial analysis
```

---

# Roadmap

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
- [ ] Data egress protection
- [ ] Secret detection
- [ ] Policy bypass detection
- [ ] Automated security tests
- [ ] Critical shutdown handling
- [ ] Tool authorization policy

## Phase 3 — Financial Data

- [ ] PostgreSQL or alternative local database
- [ ] Transaction schema
- [ ] CSV ingestion
- [ ] OFX ingestion
- [ ] Statement normalization
- [ ] Merchant normalization
- [ ] Expense categorization

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

We are not there yet but go with GNU :)

