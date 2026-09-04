# Phase 6 Financial Capability Validation

This runner validates three real agent capabilities against:

- the local PostgreSQL database;
- the approved local Ollama runtime;
- the real ToolRegistry / ToolDispatcher pipeline.

It is intended to be run after the synthetic June/July dataset has been seeded.

## Capabilities

```text
category spending
recurring expense detection
spending anomaly detection
```

## Run all

```bash
python -m scripts.validate_financial_capabilities
```

## Run one capability

```bash
python -m scripts.validate_financial_capabilities   --scenario category_spending
```

```bash
python -m scripts.validate_financial_capabilities   --scenario recurring_expenses
```

```bash
python -m scripts.validate_financial_capabilities   --scenario spending_anomalies
```

## Expected behavior

The runner prints:

- the natural-language question;
- the deterministic tools selected by the planner;
- the final answer;
- whether the expected tool was used.

The validation does not assert exact prose from the LLM.

## Seed dependency

Before running, ensure the development database contains the synthetic June/July dataset:

```bash
python -m scripts.seed_synthetic_financial_data
```

Then verify the normal test suite:

```bash
pytest -q
```
