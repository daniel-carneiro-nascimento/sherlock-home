#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re


ROOT = Path.cwd()

TARGETS = [
    "README.md",
    "docs/ROADMAP.md",
    "docs/architecture.md",
    "docs/financial-data-flow.md",
    "docs/financial-tools.md",
    "docs/testing.md",
]


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing expected repository file: {rel}")
    return path.read_text(encoding="utf-8")


def replace_section(
    text: str,
    *,
    heading: str,
    replacement: str,
) -> str:
    """
    Replace a Markdown section using its heading rather than exact body text.

    The section ends at the next heading with the same or higher level.
    This makes the updater resilient to wording changes inside the section.
    """
    match = re.match(r"^(#+)\s+", heading)
    if not match:
        raise ValueError(f"Invalid heading: {heading}")

    level = len(match.group(1))
    heading_re = re.escape(heading)

    pattern = re.compile(
        rf"(?ms)^{heading_re}\s*\n"
        rf".*?"
        rf"(?=^#{{1,{level}}}\s|\Z)"
    )

    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one section {heading!r}, found {len(matches)}"
        )

    return pattern.sub(
        replacement.rstrip() + "\n\n",
        text,
        count=1,
    )


def replace_once_regex(
    text: str,
    *,
    pattern: str,
    replacement: str,
    label: str,
    flags: int = 0,
) -> str:
    compiled = re.compile(pattern, flags)
    matches = list(compiled.finditer(text))

    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one match for {label!r}, found {len(matches)}"
        )

    return compiled.sub(
        replacement,
        text,
        count=1,
    )


# Read everything first. Nothing is written until every transformation succeeds.
original = {
    rel: read(rel)
    for rel in TARGETS
}

updated = dict(original)


# ---------------------------------------------------------------------------
# README.md
# Preserve banner, roadmap image/link, API content, and all unrelated sections.
# ---------------------------------------------------------------------------

readme = updated["README.md"]

readme = replace_once_regex(
    readme,
    pattern=r"\*\*(?:195|206|234) automated tests passing\*\*",
    replacement="**234 automated tests passing**",
    label="README automated-test baseline",
)

readme = replace_once_regex(
    readme,
    pattern=r"Current validated baseline:\s*\n\s*```text\s*\n\s*(?:195|206|234) passed\s*\n\s*```",
    replacement=(
        "Current validated baseline:\n\n"
        "```text\n"
        "234 passed\n"
        "```"
    ),
    label="README validated baseline",
    flags=re.MULTILINE,
)

current_status_heading = "## Current Status"
status_section = """## Current Status

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
- **234 automated tests passing**.

The detailed project plan lives outside this README:

**[View the Roadmap](docs/ROADMAP.md)**

[![Sherlock Home Roadmap](docs/assets/roadmap.svg)](docs/ROADMAP.md)
"""
readme = replace_section(
    readme,
    heading=current_status_heading,
    replacement=status_section,
)

testing_section = """## Testing

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
"""
readme = replace_section(
    readme,
    heading="## Testing",
    replacement=testing_section,
)

frontier_section = """## Current Development Frontier

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
"""
readme = replace_section(
    readme,
    heading="## Current Development Frontier",
    replacement=frontier_section,
)

# Update only the financial-tools documentation description if present.
readme = re.sub(
    r"(?m)^- \*\*\[Financial tools\]\(docs/financial-tools\.md\)\*\* — .+$",
    "- **[Financial tools](docs/financial-tools.md)** — implemented deterministic analysis services and Phase 6 integration boundary",
    readme,
    count=1,
)

updated["README.md"] = readme


# ---------------------------------------------------------------------------
# docs/ROADMAP.md
# ---------------------------------------------------------------------------

roadmap = updated["docs/ROADMAP.md"]

# Keep the existing visual roadmap reference and all completed earlier phases.
roadmap = roadmap.replace(
    "- **PLANNED** — not yet started as a dedicated project phase.",
    "- **NEXT** — the next major implementation phase.\n"
    "- **PLANNED** — not yet started as a dedicated project phase.",
    1,
)

phase5 = """## Phase 5 — Financial Tools — DONE

- [x] Monthly spending
- [x] Category spending
- [x] Spending comparison
- [x] Recurring expenses
- [x] Cash-flow analysis
- [x] Anomaly detection

Implemented deterministic service functions:

```text
get_monthly_spending()
get_category_spending()
compare_monthly_spending()
find_recurring_expenses()
get_cash_flow()
detect_spending_anomalies()
```

**Validated project baseline after Phase 5:**

```text
234 passed
```

**Outcome:** persisted canonical transactions can now be analyzed through deterministic, structured, API-independent financial primitives without giving the LLM direct database arithmetic responsibility.

Detailed implementation: [`financial-tools.md`](financial-tools.md).

---
"""
roadmap = replace_section(
    roadmap,
    heading="## Phase 5 — Financial Tools — NEXT",
    replacement=phase5,
)

phase6 = """## Phase 6 — Agentic Layer — NEXT

- [ ] Tool registry
- [ ] Tool dispatcher
- [ ] Deterministic tool execution
- [ ] Structured tool responses
- [ ] Agent reasoning
- [ ] Financial workflows
- [ ] Tool permission boundaries

**Goal:** allow the local LLM to reason over approved deterministic tools without allowing the model to bypass authorization, issue arbitrary SQL, or replace deterministic financial calculations.

### Recommended implementation order

```text
1. define financial tool registry/contracts
2. implement tool dispatcher
3. connect existing deterministic tool authorization
4. serialize structured financial-tool results
5. add agent orchestration over approved tools
6. add financial workflows
7. validate permission and prompt-injection boundaries
```

---
"""
roadmap = replace_section(
    roadmap,
    heading="## Phase 6 — Agentic Layer — PLANNED",
    replacement=phase6,
)

frontier = """## Current Development Frontier

The next implementation target is:

```text
Phase 6
    ↓
Agentic Layer
    ↓
Tool registry / dispatcher
    ↓
Deterministic tool authorization
    ↓
Structured financial-tool execution
```

Two ingestion extensions remain independently open in Phase 3:

```text
CSV ingestion
OFX ingestion
```

They can be implemented as parser/input adapters as long as they feed the same canonical deterministic financial pipeline.
"""
roadmap = replace_section(
    roadmap,
    heading="## Current Development Frontier",
    replacement=frontier,
)

# Append the Phase 6 invariant only if not already present.
if "Agentic execution must use an approved tool registry" not in roadmap:
    roadmap = replace_once_regex(
        roadmap,
        pattern=(
            r"(10\. Derived analytical results must be reproducible from "
            r"persisted canonical transactions and explicit query parameters\.)"
        ),
        replacement=(
            r"\1\n"
            "11. Agentic execution must use an approved tool registry rather "
            "than arbitrary code, SQL, shell, or unrestricted Python execution."
        ),
        label="ROADMAP architectural invariant 10",
    )

updated["docs/ROADMAP.md"] = roadmap


# ---------------------------------------------------------------------------
# docs/financial-tools.md
# This document was the Phase 5 design document; it now becomes the
# implementation reference for the completed phase.
# ---------------------------------------------------------------------------

financial_tools = """# Financial Tools

## Status

**Phase 5 — Financial Tools is implemented and validated.**

Current validated project baseline:

```text
234 passed
```

Implementation:

```text
app/services/financial_analysis.py
tests/test_financial_analysis.py
```

Implemented deterministic primitives:

```text
get_monthly_spending()
get_category_spending()
compare_monthly_spending()
find_recurring_expenses()
get_cash_flow()
detect_spending_anomalies()
```

No Phase 5 implementation required a database schema or Alembic migration.

---

## Architectural Boundary

Financial tools are deterministic application logic.

```text
PostgreSQL canonical transactions
    ↓
deterministic financial tool
    ↓
structured result
    ↓
authenticated API and/or approved tool dispatcher
    ↓
LLM interpretation when needed
```

The LLM must not independently recompute financial totals from transaction text when deterministic software can provide the result.

Responsibilities remain separate:

```text
service
    queries and calculates

tool adapter / dispatcher
    exposes an approved deterministic operation

API
    handles HTTP, authentication, authorization, and serialization

LLM
    interprets structured results
```

Phase 5 intentionally stops at the deterministic service boundary. Phase 6 will expose these services through an approved agent/tool-dispatch path.

---

## Shared Invariants

All Phase 5 tools preserve these rules:

1. Monetary arithmetic uses Python `Decimal` and PostgreSQL fixed-precision values.
2. Query boundaries are explicit and reproducible.
3. Transaction selection is deterministic.
4. `transaction_type`, `category`, and merchant semantics come from persisted canonical data.
5. Tools return structured data rather than prose.
6. The financial-analysis layer does not require LLM access.
7. Database credentials remain outside LLM context.
8. Empty-result behavior is explicit.
9. Tests use synthetic transactions in the isolated test database.
10. Financial tools do not mutate persisted financial records.
11. Transfers are not silently treated as spending or income.
12. Analytical spending totals are exposed as positive magnitudes while source transaction signs remain preserved in persistence.

---

## 1. Monthly Spending

Implemented interface:

```python
get_monthly_spending(
    session,
    *,
    year: int,
    month: int,
) -> MonthlySpendingResult
```

Only `transaction_type="expense"` contributes to monthly spending.

The query uses a half-open calendar interval:

```text
date >= first day of requested month
date < first day of next month
```

Income and transfers are excluded.

Persisted source debit signs remain unchanged. Analytical spending is returned as a positive magnitude.

An empty month produces:

```text
transaction_count = 0
total = Decimal("0.00")
```

---

## 2. Category Spending

Implemented interface:

```python
get_category_spending(
    session,
    *,
    year: int,
    month: int,
) -> CategorySpendingResult
```

Only expense transactions participate.

`category=None` remains explicit. Sherlock Home does not invent `"other"` or `"unknown"`.

Category rows are sorted deterministically by total descending and then category name.

---

## 3. Spending Comparison

Implemented interface:

```python
compare_monthly_spending(
    session,
    *,
    base_year: int,
    base_month: int,
    comparison_year: int,
    comparison_month: int,
) -> SpendingComparisonResult
```

The implementation reuses `get_monthly_spending()` instead of duplicating monthly aggregation.

It returns:

```text
base period
comparison period
absolute difference
percentage difference
```

If the comparison period is zero:

```text
percentage_difference = None
```

No arbitrary or infinite percentage is fabricated.

---

## 4. Recurring Expenses

Implemented interface:

```python
find_recurring_expenses(
    session,
    *,
    start_date: date,
    end_date: date,
    min_occurrences: int = 3,
    min_interval_days: int = 20,
    max_interval_days: int = 40,
    amount_tolerance: Decimal = Decimal("0.10"),
) -> RecurringExpensesResult
```

Recurring detection is deterministic and explainable.

Grouping uses normalized merchant when present, otherwise normalized original description.

A candidate must satisfy explicit:

- occurrence count;
- interval bounds;
- amount-tolerance rules.

Income and transfers are excluded.

No fuzzy or LLM classification is used.

---

## 5. Cash-Flow Analysis

Implemented interface:

```python
get_cash_flow(
    session,
    *,
    start_date: date,
    end_date: date,
) -> CashFlowResult
```

Movement types remain separate:

```text
income
expense
transfer
```

Transfers are counted as transfers but excluded from household net cash flow.

```text
net_cash_flow = income_total - expense_total
```

Expense totals are exposed as positive analytical magnitudes.

---

## 6. Deterministic Anomaly Detection

Implemented interface:

```python
detect_spending_anomalies(
    session,
    *,
    start_date: date,
    end_date: date,
    min_history: int = 3,
    threshold_multiplier: Decimal = Decimal("2.00"),
) -> SpendingAnomaliesResult
```

For each candidate expense, the detector uses prior history in this order:

```text
merchant history
    ↓ if merchant unavailable
category history
```

A candidate requires at least `min_history` prior matching expenses.

A transaction is reported when its positive spending magnitude meets or exceeds:

```text
historical average × threshold_multiplier
```

Transactions without a merchant or category basis are not guessed into a baseline.

No LLM participates in detection.

---

## Date-Range Validation

Range-based tools use:

```text
start_date <= transaction_date < end_date
```

and reject:

```text
end_date <= start_date
```

Recurrence and anomaly configuration values are validated before execution.

---

## Testing

Phase 5 coverage lives in:

```text
tests/test_financial_analysis.py
```

The tests cover:

```text
monthly aggregation
income/transfer exclusion
calendar boundaries
Decimal precision
category grouping
uncategorized expenses
deterministic ordering
month comparison
zero-reference comparison
recurring merchant patterns
description fallback
irregular recurrence rejection
amount-tolerance rejection
cash-flow semantics
negative cash flow
empty periods
merchant-history anomaly detection
category-history anomaly fallback
minimum anomaly history
invalid configuration
invalid date ranges
```

Complete project baseline after Phase 5:

```text
234 passed
```

---

## Phase 6 Integration Boundary

The next execution path is:

```text
agent request
    ↓
approved tool registry
    ↓
tool dispatcher
    ↓
deterministic tool authorization
    ↓
financial-analysis service
    ↓
structured result
    ↓
LLM interpretation / explanation
```

The agent must not receive arbitrary SQL access and must not duplicate financial arithmetic already implemented in this service.
"""

updated["docs/financial-tools.md"] = financial_tools


# ---------------------------------------------------------------------------
# docs/financial-data-flow.md
# ---------------------------------------------------------------------------

flow = updated["docs/financial-data-flow.md"]

analysis_boundary = """## Analysis boundary

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
"""

flow = replace_section(
    flow,
    heading="## Analysis boundary",
    replacement=analysis_boundary,
)

updated["docs/financial-data-flow.md"] = flow


# ---------------------------------------------------------------------------
# docs/testing.md
# ---------------------------------------------------------------------------

testing = updated["docs/testing.md"]

financial_tests = """## Financial Analysis Tests

`tests/test_financial_analysis.py` validates the complete deterministic Phase 5 analysis layer in `app/services/financial_analysis.py`.

Coverage includes:

```text
monthly spending
category spending
spending comparison
recurring-expense detection
cash-flow analysis
deterministic anomaly detection
```

Important invariants include:

- only expense transactions contribute to spending totals
- income and transfer movements are excluded from spending
- transfers remain separate from household net cash flow
- analytical spending totals are positive magnitudes while persisted source signs remain unchanged
- `Decimal` precision is preserved
- month and date-range boundaries use deterministic half-open intervals
- uncategorized expenses remain `category=None`
- zero-reference spending comparison returns `percentage_difference=None`
- recurring-expense detection uses explicit occurrence, interval, and amount-tolerance rules
- recurrence prefers normalized merchant and falls back to normalized original description
- anomaly detection uses prior merchant history and falls back to category history
- insufficient history does not produce a guessed anomaly
- invalid ranges and configuration values fail deterministically

All financial-analysis test transactions are synthetic and use the isolated PostgreSQL test database.

No LLM participates in these calculations or expectations.

---
"""

if "## Financial Analysis Tests" not in testing:
    testing = replace_once_regex(
        testing,
        pattern=r"(?m)^## Fingerprint Tests\s*$",
        replacement=financial_tests + "\n## Fingerprint Tests",
        label="testing Fingerprint Tests insertion anchor",
    )

# Replace whichever exact checkpoint the current file contains near its final baseline.
baseline_pattern = re.compile(
    r"At the current checkpoint, the complete suite passes:\s*\n\s*```text\s*\n\s*\d+ passed\s*\n\s*```",
    re.MULTILINE,
)
if baseline_pattern.search(testing):
    testing = baseline_pattern.sub(
        "At the current checkpoint, the complete suite passes:\n\n"
        "```text\n"
        "234 passed\n"
        "```",
        testing,
        count=1,
    )
else:
    # Fall back to replacing the last documented '<number> passed' block.
    blocks = list(re.finditer(
        r"```text\s*\n\s*\d+ passed\s*\n\s*```",
        testing,
        re.MULTILINE,
    ))
    if not blocks:
        raise RuntimeError("Could not locate testing baseline")
    last = blocks[-1]
    testing = (
        testing[:last.start()]
        + "```text\n234 passed\n```"
        + testing[last.end():]
    )

updated["docs/testing.md"] = testing


# ---------------------------------------------------------------------------
# docs/architecture.md
# Insert a Phase 5 layer without replacing the rest of this long document.
# ---------------------------------------------------------------------------

architecture = updated["docs/architecture.md"]

phase5_architecture = """## Deterministic Financial Analysis Layer

Phase 5 adds a deterministic analysis layer above persisted canonical transactions.

```text
PostgreSQL
    ↓
app/services/financial_analysis.py
    ↓
structured financial-analysis results
    ↓
approved API / tool boundary
    ↓
Phase 6 agent orchestration
```

Implemented primitives:

```text
get_monthly_spending()
get_category_spending()
compare_monthly_spending()
find_recurring_expenses()
get_cash_flow()
detect_spending_anomalies()
```

Architectural properties:

- financial arithmetic uses deterministic application code and `Decimal`
- spending tools consume persisted transaction semantics
- transfers are not silently treated as spending or income
- recurrence and anomaly detection use explicit, explainable rules
- range validation and empty-result behavior are deterministic
- results are structured objects rather than generated prose
- the analysis layer does not require LLM access
- no Phase 5 database schema or Alembic migration was required

Phase 6 should expose these primitives through approved tool-dispatch and authorization boundaries. The agent must not receive arbitrary SQL access.

---
"""

if "## Deterministic Financial Analysis Layer" not in architecture:
    # Insert before the final planned-evolution area if present; otherwise
    # append near the end without rewriting existing architecture text.
    planned = re.search(
        r"(?m)^## \d+\. Planned Evolution\s*$|^## Planned Evolution\s*$",
        architecture,
    )
    if planned:
        architecture = (
            architecture[:planned.start()]
            + phase5_architecture
            + "\n"
            + architecture[planned.start():]
        )
    else:
        architecture = architecture.rstrip() + "\n\n---\n\n" + phase5_architecture

updated["docs/architecture.md"] = architecture


# ---------------------------------------------------------------------------
# Validate before writing.
# ---------------------------------------------------------------------------

checks = {
    "README banner preserved":
        'docs/assets/sherlock-home_banner.png' in updated["README.md"],
    "README roadmap visual preserved":
        'docs/assets/roadmap.svg' in updated["README.md"],
    "README Phase 6 frontier":
        'Phase 6 — Agentic Layer' in updated["README.md"],
    "README 234":
        '234 passed' in updated["README.md"],
    "Roadmap Phase 5 done":
        '## Phase 5 — Financial Tools — DONE' in updated["docs/ROADMAP.md"],
    "Roadmap Phase 6 next":
        '## Phase 6 — Agentic Layer — NEXT' in updated["docs/ROADMAP.md"],
    "Financial tools implementation":
        'detect_spending_anomalies()' in updated["docs/financial-tools.md"],
    "Testing Phase 5":
        '## Financial Analysis Tests' in updated["docs/testing.md"],
    "Flow Phase 6":
        'Phase 6 agent orchestration' in updated["docs/financial-data-flow.md"],
    "Architecture Phase 5":
        '## Deterministic Financial Analysis Layer' in updated["docs/architecture.md"],
}

failed = [
    name
    for name, ok in checks.items()
    if not ok
]
if failed:
    raise RuntimeError(
        "Validation failed before write: "
        + ", ".join(failed)
    )


# ---------------------------------------------------------------------------
# Write only after all transformations and validations pass.
# ---------------------------------------------------------------------------

for rel in TARGETS:
    if updated[rel] != original[rel]:
        (ROOT / rel).write_text(
            updated[rel],
            encoding="utf-8",
        )

print("Phase 5 documentation update applied successfully.")
print()
print("Updated files:")
for rel in TARGETS:
    if updated[rel] != original[rel]:
        print(f"  {rel}")

print()
print("Preservation checks:")
for name, ok in checks.items():
    print(f"  {'OK' if ok else 'FAIL'}  {name}")

print()
print("Next:")
print("  git diff --check")
print("  git diff")
print("  pytest -q")
