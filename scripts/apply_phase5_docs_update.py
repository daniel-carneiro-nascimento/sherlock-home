#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path.cwd()


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f"Missing expected repository file: {rel}")
    return path.read_text(encoding="utf-8")


def write(rel: str, content: str) -> None:
    (ROOT / rel).write_text(content, encoding="utf-8")


def replace_required(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(
            f"Could not find expected current-repo section: {label}\n"
            "No files were written after this failure point."
        )
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# README.md
# ---------------------------------------------------------------------------

readme = read("README.md")

readme = replace_required(
    readme,
    "- private HTTPS development/deployment model;\n"
    "- **195 automated tests passing**.",
    "- private HTTPS development/deployment model;\n"
    "- deterministic Phase 5 financial-analysis services;\n"
    "- monthly and category spending analysis;\n"
    "- month-to-month spending comparison;\n"
    "- deterministic recurring-expense detection;\n"
    "- deterministic cash-flow analysis;\n"
    "- deterministic anomaly detection;\n"
    "- **234 automated tests passing**.",
    "README current status",
)

readme = replace_required(
    readme,
    "Current validated baseline:\n\n"
    "```text\n"
    "195 passed\n"
    "```",
    "Current validated baseline:\n\n"
    "```text\n"
    "234 passed\n"
    "```",
    "README test baseline",
)

readme = replace_required(
    readme,
    "Coverage includes security policy, ingestion, persistence, authentication, authorization, CSRF, session lifecycle, rate limiting, opaque IDs, API contract checks, protected configuration audit behavior, and deterministic financial enrichment.",
    "Coverage includes security policy, ingestion, persistence, authentication, authorization, CSRF, session lifecycle, rate limiting, opaque IDs, API contract checks, protected configuration audit behavior, deterministic financial enrichment, and the complete Phase 5 financial-analysis service layer.",
    "README coverage",
)

old_frontier = """## Current Development Frontier

The next major functional phase is **Phase 5 — Financial Tools**.

The first implementation target is **monthly spending**, followed by category spending, recurring-expense detection, cash-flow analysis, month comparison, and anomaly detection.

CSV and OFX ingestion remain open Phase 3 adapters, but they do not block financial-tool development because the canonical Santander pipeline already persists normalized, typed, categorized transactions.

See:
- **[Roadmap](docs/ROADMAP.md)**
- **[Financial tools design](docs/financial-tools.md)**
"""

new_frontier = """## Current Development Frontier

**Phase 5 — Financial Tools is complete.**

The implemented deterministic service layer now provides:

```text
get_monthly_spending()
get_category_spending()
compare_monthly_spending()
find_recurring_expenses()
get_cash_flow()
detect_spending_anomalies()
```

The next major functional phase is **Phase 6 — Agentic Layer**, beginning with an approved tool registry/dispatcher, deterministic tool authorization, structured tool execution, and agent orchestration over these existing financial primitives.

CSV and OFX ingestion remain open Phase 3 adapters, but they do not block Phase 6 because the canonical Santander pipeline already persists normalized, typed, categorized transactions.

See:
- **[Roadmap](docs/ROADMAP.md)**
- **[Financial tools](docs/financial-tools.md)**
"""

readme = replace_required(
    readme,
    old_frontier,
    new_frontier,
    "README development frontier",
)

readme = readme.replace(
    "- **[Financial tools](docs/financial-tools.md)** — deterministic analysis-tool contracts and Phase 5 implementation order",
    "- **[Financial tools](docs/financial-tools.md)** — implemented deterministic analysis services and Phase 6 integration boundary",
)

write("README.md", readme)


# ---------------------------------------------------------------------------
# docs/testing.md
# ---------------------------------------------------------------------------

testing = read("docs/testing.md")

financial_test_section = """## Financial Analysis Tests

`tests/test_financial_analysis.py` validates the complete deterministic Phase 5 analysis layer in `app/services/financial_analysis.py`.

The tests cover:

```text
monthly spending
category spending
spending comparison
recurring-expense detection
cash-flow analysis
deterministic anomaly detection
```

Important invariants include:

- only `transaction_type="expense"` contributes to spending totals
- income and transfer movements are excluded from spending
- transfers remain separate from household net cash flow
- analytical spending totals are positive magnitudes while persisted source signs remain unchanged
- `Decimal` precision is preserved
- month and date-range boundaries use deterministic half-open intervals
- uncategorized expenses remain `category=None`
- spending comparison returns `percentage_difference=None` when the reference period is zero
- recurring-expense detection uses explicit occurrence, interval, and amount-tolerance rules
- recurring detection prefers normalized merchant and falls back to normalized original description
- anomaly detection uses prior merchant history and falls back to category history
- insufficient anomaly history does not produce a guess
- invalid ranges and configuration values fail deterministically

The financial-analysis tests use only synthetic transactions in the isolated PostgreSQL test database.

No LLM participates in these calculations or test expectations.

---

"""

anchor = "## Database Integration Test Isolation\n"
if "## Financial Analysis Tests\n" not in testing:
    testing = replace_required(
        testing,
        anchor,
        financial_test_section + anchor,
        "testing financial analysis insertion point",
    )

testing = replace_required(
    testing,
    "Runtime financial pipeline tests\n"
    "    ↓\n"
    "production-oriented deterministic orchestration\n\n"
    "Fingerprint tests",
    "Runtime financial pipeline tests\n"
    "    ↓\n"
    "production-oriented deterministic orchestration\n\n"
    "Financial analysis tests\n"
    "    ↓\n"
    "deterministic Phase 5 calculations and analytical invariants\n\n"
    "Fingerprint tests",
    "testing layer diagram",
)

testing = replace_required(
    testing,
    "At the current checkpoint, the complete suite passes:\n\n"
    "```text\n"
    "152 passed\n"
    "```",
    "At the current checkpoint, the complete suite passes:\n\n"
    "```text\n"
    "234 passed\n"
    "```",
    "testing baseline",
)

write("docs/testing.md", testing)


# ---------------------------------------------------------------------------
# docs/financial-data-flow.md
# ---------------------------------------------------------------------------

flow = read("docs/financial-data-flow.md")

old_analysis = """## Analysis boundary

With canonical transactions persisted, Phase 5 begins above the ingestion layer:

```text
Local PostgreSQL
    ↓
Deterministic Financial Tools
    ↓
Authenticated application/API boundary
    ↓
Future agent orchestration
    ↓
LLM interpretation/explanation
```

Financial tools must query persisted canonical data. They must not re-parse statements or ask the LLM to calculate totals.
The first Phase 5 target is monthly spending. Its contract and the common rules for later analytical tools are documented in [`financial-tools.md`](financial-tools.md).
"""

new_analysis = """## Analysis boundary

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
LLM interpretation/explanation
```

Financial tools query persisted canonical data. They do not re-parse statements or ask the LLM to calculate totals.

Phase 5 is complete and validated as part of the `234 passed` project baseline. Its implemented contracts are documented in [`financial-tools.md`](financial-tools.md).

Phase 6 must consume these deterministic primitives through an approved tool registry/dispatcher rather than exposing arbitrary SQL or duplicating financial arithmetic in the LLM.
"""

flow = replace_required(
    flow,
    old_analysis,
    new_analysis,
    "financial data flow analysis boundary",
)

write("docs/financial-data-flow.md", flow)


# ---------------------------------------------------------------------------
# docs/architecture.md
# ---------------------------------------------------------------------------

architecture = read("docs/architecture.md")

phase5_arch = """## Deterministic Financial Analysis Layer

Phase 5 adds a deterministic analysis layer above persisted canonical transactions.

```text
PostgreSQL
    ↓
app/services/financial_analysis.py
    ↓
structured financial-analysis results
    ↓
approved API/tool boundary
    ↓
future agent orchestration
```

The implemented primitives are:

```text
get_monthly_spending()
get_category_spending()
compare_monthly_spending()
find_recurring_expenses()
get_cash_flow()
detect_spending_anomalies()
```

The layer does not require LLM access.

Important architectural properties:

- financial arithmetic uses deterministic application code and `Decimal`
- spending tools operate on persisted `transaction_type`, category, and merchant semantics
- transfers are not silently treated as spending or income
- recurrence and anomaly detection use explicit, explainable rules
- range validation and empty-result behavior are deterministic
- results are structured objects rather than generated prose
- no Phase 5 database schema or Alembic migration was required

Phase 6 should expose these primitives through approved tool-dispatch and authorization boundaries. The agent must not receive arbitrary SQL access.

---

"""

planned_anchor = "## 23. Planned Evolution\n"
if "## Deterministic Financial Analysis Layer\n" not in architecture:
    architecture = replace_required(
        architecture,
        planned_anchor,
        phase5_arch + planned_anchor,
        "architecture Phase 5 insertion point",
    )

old_later = """Later phases will add deterministic financial tools such as:

```text
monthly spending
category totals
recurring expenses
cash-flow analysis
month comparison
anomaly detection
```

Agentic execution should only be added after the deterministic tools and permission boundaries are in place.
"""

new_later = """The deterministic Phase 5 financial tools are now implemented:

```text
monthly spending
category spending
spending comparison
recurring expenses
cash-flow analysis
anomaly detection
```

The next major architecture stage is Phase 6 agentic orchestration over these approved deterministic tools.

Agentic execution must preserve the existing tool-authorization boundary and must not give the LLM arbitrary SQL, shell, or unrestricted Python execution.
"""

architecture = replace_required(
    architecture,
    old_later,
    new_later,
    "architecture planned financial tools",
)

write("docs/architecture.md", architecture)


# ---------------------------------------------------------------------------
# Replace small source-of-truth documents with Phase 5-complete versions.
# These are written last so an earlier failed assertion cannot partially
# replace them.
# ---------------------------------------------------------------------------

write("docs/financial-tools.md", '# Financial Tools\n\n## Status\n\n**Phase 5 — Financial Tools is implemented and validated.**\n\nCurrent validated project baseline:\n\n```text\n234 passed\n```\n\nThe implementation lives in:\n\n```text\napp/services/financial_analysis.py\n```\n\nThe Phase 5 deterministic primitives are:\n\n```text\nget_monthly_spending()\nget_category_spending()\ncompare_monthly_spending()\nfind_recurring_expenses()\nget_cash_flow()\ndetect_spending_anomalies()\n```\n\nThese functions operate over persisted PostgreSQL transactions and do not require an LLM.\n\n---\n\n## Architectural Boundary\n\nFinancial tools are deterministic application logic.\n\n```text\nPostgreSQL canonical transactions\n    ↓\ndeterministic financial tool\n    ↓\nstructured result\n    ↓\nauthenticated API and/or approved tool dispatcher\n    ↓\nLLM interpretation when needed\n```\n\nThe LLM must not independently recompute financial totals from transaction text when a deterministic tool can provide the answer.\n\nThe service, tool adapter, API, and LLM have separate responsibilities:\n\n```text\nservice\n    queries and calculates\n\ntool adapter\n    exposes an approved deterministic operation\n\nAPI route\n    handles HTTP/authentication/serialization\n\nLLM\n    interprets a structured result\n```\n\nThe current implementation intentionally stops at the deterministic service boundary. Phase 6 will expose these services through an approved agent/tool-dispatch path.\n\n---\n\n## Shared Invariants\n\nAll Phase 5 tools preserve the following rules:\n\n1. Monetary arithmetic uses Python `Decimal` and PostgreSQL fixed-precision values.\n2. Query boundaries are explicit and reproducible.\n3. Transaction selection is deterministic.\n4. `transaction_type`, `category`, and merchant semantics come from persisted canonical data.\n5. Tools return structured data rather than prose.\n6. The financial-analysis layer does not require LLM access.\n7. Database credentials remain outside LLM context.\n8. Empty-result behavior is explicit.\n9. Tests use synthetic transactions in the isolated test database.\n10. Financial tools do not mutate persisted financial records.\n11. Transfers are not silently treated as spending or income.\n12. Analytical spending totals are exposed as positive magnitudes while source transaction signs remain preserved in persistence.\n\n---\n\n## 1. Monthly Spending\n\n### Implemented interface\n\n```python\nget_monthly_spending(\n    session,\n    *,\n    year: int,\n    month: int,\n) -> MonthlySpendingResult\n```\n\nMonthly spending includes only:\n\n```text\ntransaction_type = expense\n```\n\nfor the requested calendar month.\n\nIncome and transfer movements are excluded.\n\nThe query uses a half-open calendar interval:\n\n```text\ntransaction_date >= first day of requested month\ntransaction_date < first day of next month\n```\n\nThis avoids month-length and year-boundary special cases.\n\n### Result\n\n`MonthlySpendingResult` contains:\n\n```text\nyear\nmonth\nstart_date\nend_date\ntransaction_count\ntotal\n```\n\nThe analytical spending convention is:\n\n```text\npersisted debit: -23.50\nreported spending: 23.50\n```\n\nAn empty month returns:\n\n```text\ntransaction_count = 0\ntotal = Decimal("0.00")\n```\n\n---\n\n## 2. Category Spending\n\n### Implemented interface\n\n```python\nget_category_spending(\n    session,\n    *,\n    year: int,\n    month: int,\n) -> CategorySpendingResult\n```\n\nOnly expense transactions participate.\n\nThe result groups spending by persisted expense category and returns both category-level totals and the overall monthly total.\n\n`category=None` remains explicit. Sherlock Home does not invent an `"other"` or `"unknown"` category.\n\nCategory rows are sorted deterministically by spending total descending and then by category name.\n\n### Result\n\n```text\nCategorySpendingResult\n├── year\n├── month\n├── start_date\n├── end_date\n├── transaction_count\n├── total\n└── categories[]\n    ├── category\n    ├── transaction_count\n    └── total\n```\n\n---\n\n## 3. Spending Comparison\n\n### Implemented interface\n\n```python\ncompare_monthly_spending(\n    session,\n    *,\n    base_year: int,\n    base_month: int,\n    comparison_year: int,\n    comparison_month: int,\n) -> SpendingComparisonResult\n```\n\nComparison reuses `get_monthly_spending()` instead of reimplementing monthly aggregation.\n\nThe result includes:\n\n```text\nbase period\ncomparison period\nabsolute difference\npercentage difference\n```\n\nPercentage difference is calculated relative to the comparison period.\n\nIf the comparison period total is zero:\n\n```text\npercentage_difference = None\n```\n\nSherlock Home does not fabricate an infinite or arbitrary percentage.\n\n---\n\n## 4. Recurring Expenses\n\n### Implemented interface\n\n```python\nfind_recurring_expenses(\n    session,\n    *,\n    start_date: date,\n    end_date: date,\n    min_occurrences: int = 3,\n    min_interval_days: int = 20,\n    max_interval_days: int = 40,\n    amount_tolerance: Decimal = Decimal("0.10"),\n) -> RecurringExpensesResult\n```\n\nRecurring-expense detection is deterministic and explainable.\n\nTransactions are grouped by:\n\n```text\nmerchant\n```\n\nwhen a normalized merchant exists, otherwise by normalized original description.\n\nA candidate must satisfy:\n\n- minimum occurrence count;\n- interval bounds between consecutive transactions;\n- amount variation within the configured tolerance.\n\nIncome and transfer movements are excluded.\n\nThe detector does not use fuzzy LLM classification.\n\n### Result\n\nEach candidate reports:\n\n```text\nkey\nmatch_basis\ntransaction_count\nfirst_date\nlast_date\naverage_amount\naverage_interval_days\n```\n\n---\n\n## 5. Cash-Flow Analysis\n\n### Implemented interface\n\n```python\nget_cash_flow(\n    session,\n    *,\n    start_date: date,\n    end_date: date,\n) -> CashFlowResult\n```\n\nThe tool keeps movement types separate:\n\n```text\nincome\nexpense\ntransfer\n```\n\nTransfers are counted as transfers but are excluded from net household cash flow.\n\nThe deterministic calculation is:\n\n```text\nnet_cash_flow = income_total - expense_total\n```\n\nExpense totals are exposed as positive analytical magnitudes.\n\n### Result\n\n```text\nstart_date\nend_date\nincome_count\nexpense_count\ntransfer_count\nincome_total\nexpense_total\nnet_cash_flow\n```\n\n---\n\n## 6. Deterministic Anomaly Detection\n\n### Implemented interface\n\n```python\ndetect_spending_anomalies(\n    session,\n    *,\n    start_date: date,\n    end_date: date,\n    min_history: int = 3,\n    threshold_multiplier: Decimal = Decimal("2.00"),\n) -> SpendingAnomaliesResult\n```\n\nAnomaly detection remains deterministic.\n\nFor each candidate expense, the detector uses prior history in this order:\n\n```text\nnormalized merchant history\n    ↓ if merchant is unavailable\ncategory history\n```\n\nA transaction is reported when its positive spending magnitude meets or exceeds:\n\n```text\nhistorical average × threshold_multiplier\n```\n\nThe candidate must have at least `min_history` prior matching expenses.\n\nTransactions without a merchant or category basis are not guessed into a baseline.\n\n### Result\n\nEach anomaly includes:\n\n```text\ntransaction_id\ntransaction_date\nmerchant\ncategory\namount\nbaseline_amount\nthreshold_amount\nbaseline_count\nmatch_basis\n```\n\nThe detector does not use an LLM. A future agent may explain a deterministic anomaly result but must not replace the detector.\n\n---\n\n## Date-Range Validation\n\nRange-based tools use a half-open interval:\n\n```text\nstart_date <= transaction_date < end_date\n```\n\nand reject:\n\n```text\nend_date <= start_date\n```\n\nConfiguration values such as recurrence intervals, amount tolerance, history size, and anomaly multiplier are validated before query execution.\n\n---\n\n## Testing\n\nPhase 5 is covered in:\n\n```text\ntests/test_financial_analysis.py\n```\n\nThe tests cover:\n\n```text\nmonthly aggregation\nincome/transfer exclusion\ncalendar boundaries\nDecimal precision\ncategory grouping\nuncategorized expenses\ndeterministic ordering\nmonth comparison\nzero-reference comparison\nrecurring merchant patterns\ndescription fallback\nirregular recurrence rejection\namount-tolerance rejection\ncash-flow semantics\nnegative cash flow\nempty periods\nmerchant-history anomaly detection\ncategory-history anomaly fallback\nminimum anomaly history\ninvalid configuration\ninvalid date ranges\n```\n\nThe complete project suite after Phase 5:\n\n```text\n234 passed\n```\n\nNo Phase 5 implementation required a database schema or Alembic migration.\n\n---\n\n## Phase 6 Integration\n\nThe next boundary is:\n\n```text\nagent request\n    ↓\ntool dispatcher\n    ↓\ndeterministic tool authorization\n    ↓\napproved financial tool\n    ↓\nstructured result\n    ↓\nLLM interpretation/explanation\n```\n\nThe agent must not receive arbitrary SQL access and must not duplicate financial arithmetic already implemented in this service.\n')
write("docs/ROADMAP.md", '# Sherlock Home Roadmap\n\nThis document is the source of truth for Sherlock Home development phases.\n\nThe README intentionally contains only a concise project overview. This file tracks completed work, remaining work, and the intended order of future capabilities.\n\n## Status Legend\n\n- **DONE** — the planned scope for the phase is implemented and validated.\n- **IN PROGRESS** — core capability exists, but listed work remains.\n- **NEXT** — the next major implementation phase.\n- **PLANNED** — not yet started as a dedicated project phase.\n\n---\n\n## Phase 1 — Local Runtime — DONE\n\n- [x] Local LLM runtime\n- [x] Local inference validated\n- [x] Ollama integration\n- [x] Qwen3 integration\n- [x] FastAPI\n- [x] Local project context\n- [x] Deterministic security enforcement\n\n**Outcome:** Sherlock Home can run locally with an approved local LLM while deterministic application code remains in control of protected behavior.\n\n---\n\n## Phase 2 — Security — DONE\n\n- [x] Approved model validation\n- [x] Approved local destination validation\n- [x] Sanitized security event logging\n- [x] Controlled policy exceptions\n- [x] Data egress protection\n- [x] Secret detection\n- [x] Policy bypass detection\n- [x] Automated security tests\n- [x] Runtime compromise state\n- [x] Fail-closed behavior after critical violations\n- [x] Controlled shutdown request state\n- [x] FastAPI/Uvicorn graceful shutdown lifecycle integration\n- [x] Tool authorization policy\n\n**Outcome:** the LLM is not a security authority. Deterministic policy decides whether protected operations may execute.\n\n---\n\n## Phase 3 — Financial Data — IN PROGRESS\n\n- [x] Local PostgreSQL database\n- [x] SQLAlchemy integration\n- [x] Alembic migrations\n- [x] Transaction schema\n- [x] Santander PDF statement ingestion\n- [x] Transaction fingerprinting\n- [x] Idempotent statement import\n- [x] Statement normalization\n- [x] Transaction typing\n- [x] Category taxonomy and deterministic rule priority\n- [x] Merchant normalization\n- [x] Expense categorization\n- [ ] CSV ingestion\n- [ ] OFX ingestion\n\n**Outcome so far:** a deterministic end-to-end Santander ingestion pipeline persists normalized, typed, categorized transactions without duplicate imports.\n\n**Remaining scope:** add CSV and OFX ingestion adapters without weakening the canonical normalization and safety boundaries.\n\nThese adapters do not block later phases because persisted canonical transactions already support deterministic analysis.\n\n---\n\n## Phase 4 — Authenticated Local API — DONE\n\n- [x] Define `/api/v1` router boundary\n- [x] Add single-household user model\n- [x] Add server-side session model\n- [x] Add local admin bootstrap workflow\n- [x] Add Argon2id password hashing\n- [x] Add login/logout/me endpoints\n- [x] Add secure `__Host-`, HttpOnly, SameSite session cookies\n- [x] Add CSRF protection\n- [x] Add source-aware login rate limiting/backoff\n- [x] Add authentication dependency\n- [x] Add authorization dependency\n- [x] Add OpenAPI security scheme\n- [x] Add 401/403 security tests\n- [x] Add category-rule management endpoints\n- [x] Add merchant-alias management endpoints\n- [x] Add opaque public IDs for configuration resources\n- [x] Add persistent protected configuration audit events\n- [x] Add session TTL, idle timeout, revocation, logout-all, and password rotation\n- [x] Document private HTTPS deployment\n- [x] Prepare UI-facing API contract\n\nAdditional validated hardening:\n\n- [x] Generic authentication failures for unknown/disabled users\n- [x] Argon2 dummy verification to reduce username timing leakage\n- [x] Session cleanup service\n- [x] Atomic configuration mutation + audit persistence\n- [x] OpenAPI contract regression tests\n- [x] Manual HTTPS authentication/session validation\n- [x] Manual login throttling/backoff validation\n\n**Outcome:** Sherlock Home has a versioned, authenticated, CSRF-protected, audited API suitable for a future same-origin household UI over private HTTPS.\n\n---\n\n## Phase 5 — Financial Tools — DONE\n\n- [x] Monthly spending\n- [x] Category spending\n- [x] Spending comparison\n- [x] Recurring expenses\n- [x] Cash-flow analysis\n- [x] Anomaly detection\n\nImplemented deterministic service functions:\n\n```text\nget_monthly_spending()\nget_category_spending()\ncompare_monthly_spending()\nfind_recurring_expenses()\nget_cash_flow()\ndetect_spending_anomalies()\n```\n\n**Validated project baseline after Phase 5:**\n\n```text\n234 passed\n```\n\n**Outcome:** persisted canonical transactions can now be analyzed through deterministic, structured, API-independent financial primitives without giving the LLM direct database arithmetic responsibility.\n\nDetailed implementation: [`financial-tools.md`](financial-tools.md).\n\n---\n\n## Phase 6 — Agentic Layer — NEXT\n\n- [ ] Tool dispatcher\n- [ ] Deterministic tool execution\n- [ ] Structured tool responses\n- [ ] Agent reasoning\n- [ ] Financial workflows\n- [ ] Tool permission boundaries\n\n**Goal:** allow the local LLM to reason over approved deterministic tools without allowing the model to bypass authorization, issue arbitrary SQL, or replace deterministic financial calculations.\n\n### Recommended implementation order\n\n```text\n1. define financial tool registry/contracts\n2. implement tool dispatcher\n3. connect existing deterministic tool authorization\n4. serialize structured financial-tool results\n5. add agent orchestration over approved tools\n6. add financial workflows\n7. validate permission and prompt-injection boundaries\n```\n\n---\n\n## Phase 7 — Local Retrieval — PLANNED\n\n- [ ] Local embeddings\n- [ ] Local vector storage\n- [ ] Financial document retrieval\n- [ ] Selective context injection\n- [ ] Retrieval security controls\n\n**Goal:** enable retrieval over local protected material without sending household information to external embedding or retrieval services.\n\n---\n\n## Phase 8 — User Interface — PLANNED\n\n- [ ] Local dashboard\n- [ ] Financial charts\n- [ ] Natural-language query interface\n- [ ] Monthly reports\n- [ ] Alerts\n- [ ] Financial insights\n\n**Goal:** provide a private household-facing interface over the authenticated API.\n\n---\n\n## Current Development Frontier\n\nThe next implementation target is:\n\n```text\nPhase 6\n    ↓\nAgentic Layer\n    ↓\nTool registry / dispatcher\n    ↓\nDeterministic tool authorization\n    ↓\nStructured financial-tool execution\n```\n\nTwo ingestion extensions remain independently open in Phase 3:\n\n```text\nCSV ingestion\nOFX ingestion\n```\n\nThey can be implemented as parser/input adapters as long as they feed the same canonical deterministic financial pipeline.\n\n## Architectural Invariants\n\nFuture phases must preserve these rules:\n\n1. Sherlock Home remains **single-household**, not public multi-tenant SaaS.\n2. Protected household data remains local/private.\n3. External LLMs, embeddings, analytics, telemetry, advertising, profiling, training, or evaluation must not receive protected household data.\n4. The LLM may propose, interpret, and explain; deterministic code authorizes and executes.\n5. Authentication, authorization, CSRF, session handling, financial calculations, and security decisions remain outside LLM control.\n6. Public-cloud deployments, if used, remain private-network/VPN-only with no direct public application ingress.\n7. PostgreSQL and the local model runtime remain private application dependencies.\n8. New bank/statement formats must be isolated behind deterministic ingestion adapters.\n9. Financial-tool arithmetic must use deterministic code and fixed-precision monetary values.\n10. Derived analytical results must be reproducible from persisted canonical transactions and explicit query parameters.\n11. Agentic execution must use an approved tool registry rather than arbitrary code, SQL, or shell execution.\n')
write("docs/README.md", '# Sherlock Home Documentation\n\nSherlock Home is documented as a **single-household, local-first system**. It is not a public SaaS or multi-tenant platform.\n\nCurrent documented milestone: **Phase 5 complete — deterministic financial tools**.\n\nThis directory contains implementation-oriented documentation for Sherlock Home.\n\nThe root `README.md` describes the project at a high level. The files here document specific subsystems and flows so implementation details can evolve without turning the project README into a monolith.\n\n## Documentation map\n\n- [`ROADMAP.md`](ROADMAP.md) — project phases, status, and current development frontier.\n- [`architecture.md`](architecture.md) — overall architecture and design principles.\n- [`financial-data-flow.md`](financial-data-flow.md) — current parser, canonical normalization, PostgreSQL-backed enrichment, persistence, and analysis boundary.\n- [`financial-tools.md`](financial-tools.md) — implemented Phase 5 deterministic financial-analysis services and contracts.\n- [`database.md`](database.md) — local PostgreSQL, SQLAlchemy, Alembic, transaction schema, runtime rule tables, test-database isolation, fingerprints, and idempotency.\n- [`API_V1.md`](API_V1.md) — authenticated API contract.\n- [`PRIVATE_HTTPS_DEPLOYMENT.md`](PRIVATE_HTTPS_DEPLOYMENT.md) — private HTTPS deployment model.\n- [`data-safety.md`](data-safety.md) — handling rules for real financial statements and extracted text.\n- [`testing.md`](testing.md) — behavior-oriented tests, database isolation, integration tests, financial-tool tests, and safety rules.\n- [`parsers/README.md`](parsers/README.md) — parser architecture and the contract for bank-specific parsers.\n- [`parsers/santander.md`](parsers/santander.md) — implemented Santander PDF parser.\n\n## Current deterministic boundary\n\n```text\nbank-specific ingestion\n    ↓\ncanonical normalization\n    ↓\ndeterministic enrichment\n    ↓\nfingerprint / idempotent persistence\n    ↓\nPostgreSQL\n    ↓\ndeterministic financial tools\n    ↓\napproved agent tool boundary\n```\n\n`transaction_type` and `category` remain separate dimensions. `expense`, `income`, and `transfer` describe movement nature; expense categories describe spending purpose.\n\nPhase 5 is complete. The current implementation frontier is **Phase 6 — Agentic Layer**, beginning with the approved financial tool registry/dispatcher and structured tool execution.\n\n## Validated baseline\n\n```text\n234 passed\n```\n\n## Releases\n\n- [`releases/v0.5.0.md`](releases/v0.5.0.md) — deterministic financial ingestion and PostgreSQL-backed local enrichment checkpoint.\n')

print("Documentation update applied successfully.")
print("Updated:")
for rel in [
    "README.md",
    "docs/README.md",
    "docs/ROADMAP.md",
    "docs/architecture.md",
    "docs/financial-data-flow.md",
    "docs/financial-tools.md",
    "docs/testing.md",
]:
    print(f"  {rel}")
print()
print("Next:")
print("  git diff")
print("  pytest -q")
