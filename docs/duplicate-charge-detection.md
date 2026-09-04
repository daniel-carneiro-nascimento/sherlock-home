# Duplicate Charge Detection

Sherlock Home can detect exact duplicate-looking expense charges as a
deterministic financial-analysis capability.

This capability is separate from statistical spending anomaly detection.

```text
detect_spending_anomalies
    -> unusual amount compared with prior history

detect_duplicate_charges
    -> multiple distinct stored expenses that look financially equivalent
```

## Exact duplicate policy

For v1.0.0, a duplicate-charge candidate requires at least two expense
transactions with all of the following:

```text
same transaction date
same normalized merchant
same signed amount
same normalized original description
distinct persisted transaction records
```

Fingerprint is deliberately **not** part of this comparison.

A transaction fingerprint exists for ingestion/idempotency identity. Two real
charges can legitimately have different fingerprints while still appearing
financially duplicated.

## Example

```text
ID 134
2026-07-15
OFICINA CENTRAL
PAGAMENTO OFICINA CENTRAL
-349.90
fingerprint A

ID 135
2026-07-15
OFICINA CENTRAL
PAGAMENTO OFICINA CENTRAL
-349.90
fingerprint B
```

The deterministic result is a **possible duplicate charge**.

It does not prove:

- merchant error;
- accidental double payment;
- unauthorized use;
- fraud.

The final responder must preserve that distinction.

## Broad suspicious-spending questions

A broad user question such as:

```text
Existem gastos suspeitos em julho de 2026?
```

should collect both deterministic signals:

```text
detect_spending_anomalies
+
detect_duplicate_charges
```

This allows one answer to surface both unusually large historical deviations
and exact duplicate-looking charges.

## Validation

After the duplicate OFICINA CENTRAL rows exist in the development database:

```bash
python -m scripts.validate_financial_capabilities   --scenario duplicate_charges
```

Then test the natural broad question:

```bash
python -m scripts.validate_financial_capabilities   --scenario suspicious_spending
```

Or directly:

```bash
python -m scripts.financial_chat   "Existem gastos suspeitos em julho de 2026?"
```

Expected evidence should include:

- the existing CAFE DO BAIRRO spending anomaly;
- the two OFICINA CENTRAL transactions as one possible duplicate-charge
  candidate.

## Database impact

None.

No SQLAlchemy model, table, index, or column changes are required.

No Alembic migration is required.
