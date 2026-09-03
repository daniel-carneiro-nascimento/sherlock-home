# Real Financial Chat CLI

This command is the first end-to-end Sherlock Home chat path that uses:

```text
user question
    ↓
approved local Ollama model
    ↓
strict ToolPlan
    ↓
ToolRegistry
    ↓
ToolDispatcher + deterministic policy
    ↓
real local PostgreSQL financial data
    ↓
structured AgentEvidence
    ↓
approved local Ollama responder
    ↓
natural-language answer
```

Unlike `scripts/smoke_test_agent.py`, this command **does use the household's real local financial database**.

It does not print raw SQL results, transaction dumps, database credentials, or intermediate evidence. By default it prints only:

- deterministic tool names used by the agent;
- the final natural-language answer.

## Before running

The following should already pass:

```bash
pytest -q
python -m scripts.smoke_test_agent
```

PostgreSQL must be running and `.env` must contain the normal Sherlock Home database and Ollama configuration.

## First real query

For the first end-to-end validation, use an explicit period known to exist in the local database.

```bash
python -m scripts.financial_chat \
  "Quanto gastei em junho de 2026?"
```

After that succeeds, try a broader analysis:

```bash
python -m scripts.financial_chat \
  "Analise meus gastos de junho de 2026 e diga em quais categorias eu poderia reduzir despesas."
```

Expected shape:

```text
Sherlock Home
-------------
Tools used: get_monthly_spending, get_category_spending

<answer generated from deterministic local evidence>
```

The exact tool list is model-planned and may vary, but every requested tool must pass the deterministic registry, permission, argument, and runtime-security checks before execution.

## Hide tool names

```bash
python -m scripts.financial_chat \
  --hide-tools \
  "Quanto gastei em junho de 2026?"
```

## Data boundary

This command intentionally crosses from the synthetic smoke-test boundary into real household data.

```text
real financial data
    ↓
deterministic local tools
    ↓
structured evidence
    ↓
approved local/private Ollama runtime only
```

Do not point `OLLAMA_HOST` at a public or third-party inference endpoint.
