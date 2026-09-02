# Santander PDF Parser

## Status

Implemented.

Main module:

```text
app/ingestion/santander_pdf.py
```

The parser was designed against Santander's consolidated statement PDF layout as rendered locally through:

```bash
pdftotext -layout statement.pdf statement.txt
```

Real statement files are never test fixtures and must not be committed.

## Statement metadata

The statement header contains a Portuguese month and year, for example a structure equivalent to:

```text
EXTRATO CONSOLIDADO INTELIGENTE
junho/2026
```

The parser maps the Portuguese month name to a month number and stores the statement month as the first day of that month.

A transaction such as `09/06` therefore receives its explicit year from statement metadata instead of guessing the year.

## Movement section

The parser locates the `Movimentação` section and requires a known structural end marker before later account-summary sections.

This is important because the PDF also contains public/commercial indicators, summaries, pending/future items, automatic-debit sections, and other monetary-looking values that are not ordinary account transactions.

The parser must not use the rule "a line containing a date or money is a transaction" across the whole document.

## Transaction lines

The statement can contain:

- an explicit date on the first transaction of a group;
- later transactions on the same date without repeating the date;
- multiline descriptions;
- optional document identifiers;
- movement values with the Brazilian decimal comma;
- negative values represented by a trailing minus sign;
- balance values only on some transaction lines.

Example synthetic monetary conversion:

```text
2.689,52  -> Decimal("2689.52")
4.121,13- -> Decimal("-4121.13")
```

A line containing a movement value starts a new transaction. A valid following line without a movement value may extend the previous transaction description.

## Repeated headers and page layout

`pdftotext -layout` preserves useful spacing but PDF page layouts can repeat table headers with different spacing. The parser explicitly ignores transaction table header lines and relies on statement-section structure rather than assuming one global character offset for the entire document.

## Sanity checks

The current parser rejects parsed transactions with suspicious description lengths and zero amounts. These checks caught an early failure mode where later non-transaction sections were being interpreted as transactions.

The preferred behavior is controlled failure rather than persisting corrupted financial records.

## Output

The parser returns a `ParsedStatement` containing a statement month and a list of `ParsedTransaction` records. Persistence is handled separately by the importer.
