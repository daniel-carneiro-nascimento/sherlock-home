# Local Model Compatibility Smoke Test

Sherlock Home includes a data-safe compatibility smoke test for approved local Ollama models.

The smoke test does **not** read the household database and does **not** use real financial data.

It validates four boundaries:

```text
approved Ollama runtime/model
    ↓
local chat response
    ↓
Sherlock Home ToolRegistry
    ↓
strict JSON ToolPlan generation
    ↓
synthetic structured financial evidence
    ↓
natural-language response
```

## Run

From the repository root:

```bash
python -m scripts.smoke_test_agent
```

The script uses the normal Sherlock Home configuration:

```env
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:14b
```

You can override those values for one smoke-test invocation:

```bash
python -m scripts.smoke_test_agent \
  --host http://127.0.0.1:11434 \
  --model qwen3:14b
```

The selected model must still be allowed by Sherlock Home's deterministic model policy.

List the currently approved models:

```bash
python -m scripts.smoke_test_agent \
  --list-approved-models
```

## Expected output

A compatible runtime/model should produce output similar to:

```text
Sherlock Home Agent Compatibility Smoke Test

Ollama endpoint : http://127.0.0.1:11434
Model           : qwen3:14b
Financial data  : synthetic only

Security / runtime.............. OK
Tool registry................... OK
Planner JSON contract........... OK
Evidence responder.............. OK

RESULT: COMPATIBLE
```

If the model cannot produce a valid Sherlock Home ToolPlan, uses the wrong deterministic tool for the fixed compatibility question, cannot satisfy endpoint/model policy, or cannot produce a final response from structured synthetic evidence, the command exits non-zero and reports:

```text
RESULT: NOT COMPATIBLE
```

## What this test proves

The smoke test verifies that:

- Ollama is reachable through the configured approved endpoint.
- The selected model is approved by deterministic security policy.
- The current financial ToolRegistry is present.
- The model can produce strict JSON that passes `parse_tool_plan()`.
- The model can select `get_monthly_spending` for a fixed, unambiguous monthly-spending question.
- The model produces the expected deterministic `year=2026` and `month=9` arguments.
- The response layer can interpret structured synthetic evidence.

## What this test does not prove

It does not:

- connect to PostgreSQL;
- read financial transactions;
- import statements;
- execute real financial tools against household data;
- validate the accuracy of financial advice;
- bypass the Sherlock Home model or endpoint allowlists.

The purpose is model/runtime compatibility, not financial-data validation.
