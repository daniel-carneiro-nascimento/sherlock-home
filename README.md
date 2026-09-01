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
