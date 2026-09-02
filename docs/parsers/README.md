# Bank Parser Architecture

## Why one parser per bank/source format?

Bank statements are not stable universal formats. Even when two banks both export PDF, CSV, or OFX, field names, page layouts, monetary notation, continuation lines, headers, and summary sections can differ.

Sherlock Home therefore isolates source-specific parsing logic.

```text
app/ingestion/
├── santander_pdf.py
├── <future_bank>_csv.py
├── <future_bank>_ofx.py
└── ...
```

A bank layout change should normally affect:

1. that bank/source parser;
2. that parser's synthetic fixture;
3. that parser's tests.

It should not require changing unrelated bank parsers.

## Parser responsibilities

A bank parser may:

- identify the statement period;
- locate the actual transaction section;
- ignore repeated page headers and non-transaction sections;
- parse source-specific dates and monetary notation;
- join valid multiline descriptions;
- distinguish a new transaction from a continuation line;
- expose source identifiers when available;
- reject suspicious or ambiguous structures.

A bank parser should not:

- categorize expenses using LLM guesses;
- embed database credentials;
- transmit statements to external services;
- silently accept malformed data just to increase the parsed transaction count;
- write directly to Git-tracked fixtures using real statement content.

## Parser output contract

Parsers should converge toward canonical structures independent of the source layout. The current Santander parser exposes `ParsedStatement` and `ParsedTransaction` structures.

Downstream import and normalization code should depend on canonical fields rather than PDF spacing or bank-specific labels.

## Fail closed

A financial parser should prefer a controlled failure over silently importing obviously corrupt records.

Examples of useful deterministic safeguards include:

- missing statement period;
- missing movement section;
- missing expected end marker;
- empty descriptions;
- suspiciously short or excessively long descriptions;
- zero-value records where the source format does not define them as transactions.

Parser validation is not a substitute for reconciliation, but it prevents known classes of layout drift from becoming stored financial facts.
