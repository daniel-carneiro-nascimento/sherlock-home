# Financial Tools

## Purpose

Phase 5 introduces deterministic financial-analysis primitives over transactions already persisted in PostgreSQL.

These tools are application logic, not LLM reasoning.

The intended boundary is:

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

The LLM must not independently recompute financial totals from transaction text when a deterministic tool can provide the answer.

## Core invariants

Every financial tool should preserve these rules:

1. Monetary arithmetic uses Python `Decimal` and PostgreSQL fixed-precision values.
2. Query boundaries are explicit and reproducible.
3. Transaction selection is deterministic.
4. `transaction_type`, `category`, and merchant semantics come from persisted canonical data.
5. Tools return structured data rather than prose.
6. The tool layer does not need LLM access.
7. Database credentials remain outside LLM context.
8. Empty-result behavior is explicit.
9. Tests verify invariants and query semantics rather than one hard-coded fixture history.
10. Financial tools do not mutate transactions unless a tool is explicitly designed as a protected write operation.

## Service placement

The initial implementation should keep query/calculation services separate from API routes.

Recommended structure:

```text
app/
├── services/
│   ├── financial_pipeline.py
│   └── financial_analysis.py
└── tools/
    └── financial.py
```

The exact split can evolve, but responsibilities should remain distinct:

```text
service
    queries and calculates

tool adapter
    exposes an approved deterministic operation

API route
    handles HTTP/authentication/serialization

LLM
    interprets a structured result
```

## Phase 5 implementation order

```text
1. monthly spending
2. category spending
3. spending comparison
4. recurring expenses
5. cash-flow analysis
6. anomaly detection
```

Monthly spending should establish the shared conventions used by the later tools.

---

## Tool 1 — Monthly Spending

### Definition

Monthly spending is the sum of persisted transactions whose:

```text
transaction_type = expense
```

and whose transaction date belongs to the requested calendar month.

Income and transfer movements are excluded.

The tool should not infer expense status from amount sign at query time. Transaction typing already belongs to the ingestion/enrichment pipeline.

### Proposed deterministic interface

A service-level interface may be conceptually shaped as:

```python
get_monthly_spending(
    session,
    *,
    year: int,
    month: int,
) -> MonthlySpendingResult
```

The exact Python name may change during implementation. The contract is more important than the function name.

### Proposed result shape

```text
MonthlySpendingResult
├── year
├── month
├── start_date
├── end_date
├── transaction_count
└── total
```

`total` should be a `Decimal`.

Because current persisted expense amounts may use debit-negative source semantics, the implementation must define one output convention and test it explicitly.

Recommended analysis convention:

```text
stored expense amount: -23.50
reported spending total: 23.50
```

In other words, analytical spending totals are positive magnitudes even if persisted source movements are negative.

This conversion belongs in deterministic application code.

### Date semantics

Calendar month boundaries should be explicit:

```text
start_date = first day of requested month
end_date = first day of next month
```

The database query should preferably use a half-open interval:

```text
date >= start_date
date < end_date
```

This avoids month-length special cases and composes cleanly with later date-range tools.

### Empty month

An empty month should produce a valid deterministic result:

```text
transaction_count = 0
total = Decimal("0.00")
```

It should not produce `None`, fabricated activity, or an LLM-generated estimate.

### Tests

The first financial-tool test set should cover at least:

```text
multiple expenses are summed
income is excluded
transfer is excluded
adjacent months are excluded
empty month returns zero
Decimal precision is preserved
reported spending uses the documented positive-magnitude convention
```

Tests should derive expected totals from synthetic test transactions inserted into the isolated test database.

Do not use real household transactions as fixtures.

---

## Tool 2 — Category Spending

This tool should build on the monthly/date-range query conventions established by monthly spending.

Conceptual output:

```text
category -> total
```

Only `transaction_type = expense` records are eligible.

`category=None` should remain explicit rather than being silently guessed.

---

## Tool 3 — Spending Comparison

Comparison should consume deterministic period totals rather than duplicate calculation logic.

For example:

```text
period A total
period B total
absolute difference
percentage difference
```

Division-by-zero behavior must be explicit.

---

## Tool 4 — Recurring Expenses

Recurring-expense detection may use deterministic merchant/description/date/amount heuristics.

A first implementation should favor transparent rules over probabilistic or LLM classification.

The result should identify why a candidate was considered recurring.

---

## Tool 5 — Cash-flow Analysis

Cash flow should treat movement types separately:

```text
income
expense
transfer
```

Transfers must not be counted as household income or expense merely because money moved between accounts.

---

## Tool 6 — Anomaly Detection

Initial anomaly detection should remain deterministic and explainable.

Examples may include:

```text
expense above configured threshold
merchant spend materially above historical deterministic baseline
category total outside an explicit statistical threshold
```

An LLM may later explain a detected anomaly, but it should not be the primary detector.

## API and agent integration

Phase 5 tools should be usable without the LLM.

The future integration path is:

```text
authenticated request
    ↓
authorization
    ↓
deterministic financial tool
    ↓
structured result
```

and later:

```text
agent requests approved tool
    ↓
tool authorization
    ↓
deterministic financial tool
    ↓
structured result
    ↓
LLM explanation
```

This keeps financial arithmetic independently testable and auditable.
