import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


MONTHS_PT = {
    "janeiro": 1,
    "fevereiro": 2,
    "março": 3,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}


@dataclass
class ParsedTransaction:
    date: date
    description: str
    document: str | None
    amount: Decimal
    balance: Decimal | None


@dataclass
class ParsedStatement:
    statement_month: date
    transactions: list[ParsedTransaction]


STATEMENT_PERIOD_RE = re.compile(
    r"\b("
    + "|".join(MONTHS_PT.keys())
    + r")/(\d{4})\b",
    re.IGNORECASE,
)

TRANSACTION_DATE_RE = re.compile(
    r"^\s*(\d{2})/(\d{2})\b"
)

MONEY_RE = re.compile(
    r"(?<!\d)"
    r"(\d{1,3}(?:\.\d{3})*,\d{2}-?)"
    r"(?!\d)"
)


def parse_brazilian_decimal(value: str) -> Decimal:
    value = value.strip()

    negative = value.endswith("-")

    if negative:
        value = value[:-1]

    value = value.replace(".", "").replace(",", ".")

    result = Decimal(value)

    if negative:
        result = -result

    return result


def parse_statement_period(text: str) -> date:
    match = STATEMENT_PERIOD_RE.search(text)

    if not match:
        raise ValueError("statement period not found")

    month_name = match.group(1).lower()
    year = int(match.group(2))

    month = MONTHS_PT[month_name]

    return date(year, month, 1)


def extract_movement_section(text: str) -> str:
    lines = text.splitlines()

    start_index: int | None = None
    end_index: int | None = None

    for index, line in enumerate(lines):
        stripped = line.strip()

        if start_index is None:
            if stripped == "Movimentação":
                start_index = index + 1
            continue

        if (
            stripped.startswith("Conta Corrente")
            and "Bloqueio" in stripped
            and "Bloqueado" in stripped
        ):
            end_index = index
            break

    if start_index is None:
        raise ValueError("movement section not found")

    if end_index is None:
        raise ValueError("movement section end not found")

    return "\n".join(
        lines[start_index:end_index]
    )


def _is_table_header(line: str) -> bool:
    normalized = line.lower()

    return (
        "data" in normalized
        and "descrição" in normalized
        and "movimento" in normalized
    )


def _is_noise_line(line: str) -> bool:
    normalized = line.strip().upper()

    if not normalized:
        return True

    noise_markers = (
        "EXTRATO CONSOLIDADO",
        "SANTANDER",
        "PÁGINA",
        "PAGINA",
    )

    return any(
        marker in normalized
        for marker in noise_markers
    )


def _extract_money_values(
    line: str,
) -> list[tuple[str, int, int]]:
    return [
        (
            match.group(1),
            match.start(),
            match.end(),
        )
        for match in MONEY_RE.finditer(line)
    ]


def _build_transaction_date(
    day: int,
    month: int,
    statement_month: date,
) -> date:
    return date(
        statement_month.year,
        month,
        day,
    )


def _extract_description_and_document(
    line: str,
    amount_start: int,
    date_match: re.Match[str] | None,
) -> tuple[str, str | None]:
    prefix = line[:amount_start].rstrip()

    if date_match:
        prefix = prefix[date_match.end():].strip()

    parts = re.split(
        r"\s{2,}",
        prefix,
    )

    parts = [
        part.strip()
        for part in parts
        if part.strip()
    ]

    if not parts:
        return "", None

    if len(parts) == 1:
        return parts[0], None

    candidate_document = parts[-1]

    if candidate_document == "-":
        document = None
    else:
        document = candidate_document

    description_parts = parts[:-1]

    description = " ".join(
        description_parts
    ).strip()

    return description, document


def parse_transactions(
    movement_text: str,
    statement_month: date,
) -> list[ParsedTransaction]:
    transactions: list[ParsedTransaction] = []

    current_date: date | None = None
    current_transaction: ParsedTransaction | None = None

    for raw_line in movement_text.splitlines():
        line = raw_line.rstrip()

        if not line.strip():
            continue

        if _is_table_header(line):
            continue

        if _is_noise_line(line):
            continue

        date_match = TRANSACTION_DATE_RE.match(line)

        if date_match:
            day = int(date_match.group(1))
            month = int(date_match.group(2))

            current_date = _build_transaction_date(
                day=day,
                month=month,
                statement_month=statement_month,
            )

        money_values = _extract_money_values(line)

        if money_values:
            if current_date is None:
                continue

            amount_text, amount_start, _ = (
                money_values[0]
            )

            balance: Decimal | None = None

            if len(money_values) >= 2:
                balance = parse_brazilian_decimal(
                    money_values[-1][0]
                )

            (
                description,
                document,
            ) = _extract_description_and_document(
                line=line,
                amount_start=amount_start,
                date_match=date_match,
            )

            if not description:
                raise ValueError(
                    "parsed transaction has empty description"
                )

            current_transaction = ParsedTransaction(
                date=current_date,
                description=description,
                document=document,
                amount=parse_brazilian_decimal(
                    amount_text
                ),
                balance=balance,
            )

            transactions.append(
                current_transaction
            )

            continue

        if current_transaction is not None:
            continuation = line.strip()

            if (
                continuation
                and len(continuation) <= 120
                and not _is_table_header(line)
                and not _is_noise_line(line)
            ):
                current_transaction.description += (
                    f" {continuation}"
                )

    for tx in transactions:
        description_length = len(
            tx.description.strip()
        )

        if description_length < 3:
            raise ValueError(
                "parsed transaction contains "
                "suspiciously short description"
            )

        if description_length > 500:
            raise ValueError(
                "parsed transaction contains "
                "suspiciously long description"
            )

        if tx.amount == 0:
            raise ValueError(
                "parsed transaction contains zero amount"
            )

    return transactions


def parse_statement(
    text: str,
) -> ParsedStatement:
    statement_month = parse_statement_period(
        text
    )

    movement_section = extract_movement_section(
        text
    )

    transactions = parse_transactions(
        movement_section,
        statement_month,
    )

    return ParsedStatement(
        statement_month=statement_month,
        transactions=transactions,
    ) 
