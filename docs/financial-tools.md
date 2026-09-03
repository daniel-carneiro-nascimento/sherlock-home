# Financial Tools

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
