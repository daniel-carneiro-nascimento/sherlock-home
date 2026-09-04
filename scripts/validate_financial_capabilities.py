from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

from app.agents.chat_service import build_financial_chat_service
from app.db.database import SessionLocal


@dataclass(frozen=True)
class Scenario:
    name: str
    question: str
    expected_tools: tuple[str, ...]


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        name="category_spending",
        question=(
            "Analise meus gastos de julho de 2026 por categoria "
            "e diga onde eu mais gastei."
        ),
        expected_tools=("get_category_spending",),
    ),
    Scenario(
        name="recurring_expenses",
        question=(
            "Quais despesas recorrentes aparecem entre junho e julho de 2026?"
        ),
        expected_tools=("find_recurring_expenses",),
    ),
    Scenario(
        name="spending_anomalies",
        question=(
            "Existem gastos anômalos entre junho e julho de 2026?"
        ),
        expected_tools=("detect_spending_anomalies",),
    ),
)


def _format_tools(tools: tuple[str, ...]) -> str:
    return ", ".join(tools) if tools else "none"


def run_scenario(*, scenario: Scenario) -> bool:
    service = build_financial_chat_service()

    with SessionLocal() as session:
        result = service.ask(
            session,
            user_message=scenario.question,
        )

    used = tuple(result.tools_used)

    print()
    print(f"[{scenario.name}]")
    print(f"Question: {scenario.question}")
    print("Tools used: " + _format_tools(used))
    print()
    print(result.answer)
    print()

    missing = [
        tool
        for tool in scenario.expected_tools
        if tool not in used
    ]

    if missing:
        print("VALIDATION: FAILED")
        print(
            "Missing expected tool(s): "
            + ", ".join(missing)
        )
        return False

    print("VALIDATION: PASSED")
    return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run real Phase 6 capability checks against the local "
            "Sherlock Home database and approved Ollama runtime."
        )
    )
    parser.add_argument(
        "--scenario",
        choices=[s.name for s in SCENARIOS],
        help="Run only one scenario. If omitted, all scenarios run.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    scenarios = SCENARIOS
    if args.scenario:
        scenarios = tuple(
            s for s in SCENARIOS
            if s.name == args.scenario
        )

    print(
        "Sherlock Home Phase 6 "
        "Financial Capability Validation"
    )
    print("Data source: real local PostgreSQL")
    print("Model: approved local Ollama runtime")

    results = [
        run_scenario(scenario=scenario)
        for scenario in scenarios
    ]

    print()

    if all(results):
        print("RESULT: ALL SELECTED CAPABILITIES PASSED")
        return 0

    print("RESULT: ONE OR MORE CAPABILITIES FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
