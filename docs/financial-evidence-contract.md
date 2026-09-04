# Financial Evidence Contract

Sherlock Home keeps financial calculations and policy decisions in
deterministic application code. The LLM receives structured evidence and
interprets it; it does not define the financial rules.

This document defines three evidence guarantees introduced before the
`v1.0.0 — Holmes-Hat` release.

## 1. Explicit currency

All financial tools now attach:

```json
{
  "currency": "BRL"
}
```

to their structured result.

The responder must use the supplied currency and must not infer a currency
when one is absent.

For Portuguese responses, `BRL` may naturally be presented as `R$`.

This prevents a model from inventing USD or another currency from numeric
values alone.

## 2. Deterministic recurrence semantics

The LLM no longer controls `min_occurrences`.

Sherlock Home derives it from the requested half-open date range:

```text
range touches 1-2 calendar months
    -> min_occurrences = 2

range touches 3+ calendar months
    -> min_occurrences = 3
```

Examples:

```text
2026-06-01 <= date < 2026-08-01
touches June + July
-> 2 occurrences required

2026-06-01 <= date < 2026-09-01
touches June + July + August
-> 3 occurrences required
```

The existing deterministic interval and amount-tolerance rules remain in
place. The model may request supported interval/tolerance parameters, but it
cannot weaken the minimum occurrence threshold.

The returned evidence includes:

```json
{
  "recurrence_policy": {
    "min_occurrences": 2,
    "calendar_month_span": 2,
    "min_interval_days": 20,
    "max_interval_days": 40,
    "amount_tolerance": "0.10"
  }
}
```

so the final answer can explain the rule that was actually applied.

## 3. Auditable anomaly explanations

The financial-analysis service already calculates deterministic anomaly
explanation fields for each flagged transaction:

```text
baseline_amount
threshold_amount
baseline_count
```

Those fields are preserved in the structured tool evidence and the active
anomaly policy is attached:

```json
{
  "anomaly_policy": {
    "min_history": 3,
    "threshold_multiplier": "2.00",
    "explanation_fields": [
      "baseline_amount",
      "threshold_amount",
      "baseline_count"
    ]
  }
}
```

The responder is explicitly instructed to use those deterministic values when
explaining why a transaction was flagged.

Example:

```text
R$ 84,90 was flagged as anomalous because the deterministic baseline was
R$ 19,84 across 5 prior matching transactions, and the active threshold was
R$ 39,68.
```

An anomaly must not be described as fraud, unauthorized use, wrongdoing, or an
error unless separate deterministic evidence supports that conclusion.

## Security boundary

The resulting flow remains:

```text
PostgreSQL
    ↓
deterministic financial service
    ↓
server-owned financial tool policy
    ↓
structured evidence
    ↓
approved local/private LLM
    ↓
natural-language explanation
```

The model does not choose the currency, recurrence threshold, anomaly
baseline, or anomaly threshold.

## Database impact

None.

This change does not modify:

- SQLAlchemy models;
- PostgreSQL schema;
- Alembic migrations;
- stored transaction rows.

No Alembic migration is required.
