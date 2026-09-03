from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Callable

from app.agents.financial_agent import AgentEvidence
from app.agents.ollama_planner import OllamaFinancialPlanner
from app.agents.ollama_responder import OllamaFinancialResponder
from app.agents.ollama_runtime import OllamaClient
from app.core.config import settings
from app.core.security import security_policy
from app.tools.registry import ToolRegistry
from app.tools.schemas import ToolExecutionResult


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str


def _ok(
    name: str,
    detail: str,
) -> CheckResult:
    return CheckResult(
        name=name,
        passed=True,
        detail=detail,
    )


def _fail(
    name: str,
    detail: str,
) -> CheckResult:
    return CheckResult(
        name=name,
        passed=False,
        detail=detail,
    )


def _run_check(
    name: str,
    function: Callable[[], str],
) -> CheckResult:
    try:
        detail = function()
    except Exception as exc:
        return _fail(
            name,
            f"{type(exc).__name__}: {exc}",
        )

    return _ok(
        name,
        detail,
    )


def _format_status(
    result: CheckResult,
) -> str:
    status = (
        "OK"
        if result.passed
        else "FAILED"
    )

    return (
        f"{result.name:.<32} "
        f"{status}"
    )


def _runtime_check(
    client: OllamaClient,
) -> str:
    response = client.chat(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a runtime health check. "
                    "Reply with the single word OK."
                ),
            },
            {
                "role": "user",
                "content": "health check",
            },
        ],
        json_mode=False,
        temperature=0.0,
    )

    if not response.strip():
        raise RuntimeError(
            "model returned an empty response"
        )

    return "local Ollama chat responded"


def _planner_check(
    client: OllamaClient,
    registry: ToolRegistry,
) -> str:
    planner = OllamaFinancialPlanner(
        client=client,
        registry=registry,
    )

    plan = planner.plan(
        (
            "I want to know the total amount "
            "I spent in September 2026. "
            "Use the appropriate Sherlock Home "
            "financial tool."
        )
    )

    if not plan.calls:
        raise RuntimeError(
            "planner returned no tool calls"
        )

    tool_names = tuple(
        call.name
        for call in plan.calls
    )

    if (
        "get_monthly_spending"
        not in tool_names
    ):
        raise RuntimeError(
            "planner did not select "
            "get_monthly_spending"
        )

    monthly_calls = [
        call
        for call in plan.calls
        if call.name
        == "get_monthly_spending"
    ]

    if len(monthly_calls) != 1:
        raise RuntimeError(
            "planner must request exactly one "
            "get_monthly_spending call"
        )

    arguments = monthly_calls[0].arguments

    if arguments != {
        "year": 2026,
        "month": 9,
    }:
        raise RuntimeError(
            "planner produced unexpected monthly "
            f"arguments: {arguments!r}"
        )

    return (
        "valid ToolPlan: "
        + ", ".join(tool_names)
    )


def _registry_check(
    registry: ToolRegistry,
) -> str:
    names = registry.names()

    required = {
        "get_monthly_spending",
        "get_category_spending",
        "compare_monthly_spending",
        "find_recurring_expenses",
        "get_cash_flow",
        "detect_spending_anomalies",
    }

    missing = required - set(names)

    if missing:
        raise RuntimeError(
            "missing registered tool(s): "
            + ", ".join(
                sorted(missing)
            )
        )

    return (
        f"{len(names)} approved financial "
        "tools available"
    )


def _responder_check(
    client: OllamaClient,
) -> str:
    responder = OllamaFinancialResponder(
        client=client
    )

    evidence = AgentEvidence(
        user_message=(
            "How much did I spend in "
            "September 2026?"
        ),
        tool_results=(
            ToolExecutionResult(
                tool_name=(
                    "get_monthly_spending"
                ),
                data={
                    "year": 2026,
                    "month": 9,
                    "start_date": (
                        "2026-09-01"
                    ),
                    "end_date": (
                        "2026-10-01"
                    ),
                    "transaction_count": 4,
                    "total": "123.45",
                },
            ),
        ),
        answer_instruction=(
            "Answer using only the "
            "deterministic evidence."
        ),
    )

    answer = responder.respond(
        evidence
    )

    if not answer.strip():
        raise RuntimeError(
            "responder returned an empty answer"
        )

    return (
        "structured evidence produced "
        "a natural-language answer"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate an approved local Ollama "
            "model against Sherlock Home's "
            "agent-planning contract without "
            "using real financial data."
        )
    )

    parser.add_argument(
        "--host",
        default=settings.ollama_host,
        help=(
            "Ollama endpoint. Defaults to "
            "OLLAMA_HOST from Sherlock Home "
            "configuration."
        ),
    )

    parser.add_argument(
        "--model",
        default=settings.ollama_model,
        help=(
            "Ollama model. Defaults to "
            "OLLAMA_MODEL from Sherlock Home "
            "configuration."
        ),
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help=(
            "Ollama request timeout in seconds "
            "(default: 120)."
        ),
    )

    parser.add_argument(
        "--list-approved-models",
        action="store_true",
        help=(
            "Print the deterministic Sherlock "
            "Home model allowlist and exit."
        ),
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.list_approved_models:
        print(
            "Sherlock Home approved models:"
        )

        for model in sorted(
            security_policy.APPROVED_MODELS
        ):
            print(f"  - {model}")

        return 0

    print(
        "Sherlock Home Agent Compatibility "
        "Smoke Test"
    )
    print()
    print(f"Ollama endpoint : {args.host}")
    print(f"Model           : {args.model}")
    print(
        "Financial data  : synthetic only"
    )
    print()

    registry = ToolRegistry()

    client = OllamaClient(
        host=args.host,
        model=args.model,
        timeout_seconds=args.timeout,
    )

    checks = [
        _run_check(
            "Security / runtime",
            lambda: _runtime_check(
                client
            ),
        ),
        _run_check(
            "Tool registry",
            lambda: _registry_check(
                registry
            ),
        ),
        _run_check(
            "Planner JSON contract",
            lambda: _planner_check(
                client,
                registry,
            ),
        ),
        _run_check(
            "Evidence responder",
            lambda: _responder_check(
                client
            ),
        ),
    ]

    for result in checks:
        print(
            _format_status(result)
        )

        if not result.passed:
            print(
                f"  {result.detail}"
            )

    print()

    failed = [
        result
        for result in checks
        if not result.passed
    ]

    if failed:
        print(
            "RESULT: NOT COMPATIBLE"
        )
        print(
            "The configured runtime/model did "
            "not satisfy the current Sherlock "
            "Home agent contract."
        )
        return 1

    print("RESULT: COMPATIBLE")
    print(
        "The configured local model satisfied "
        "the current Sherlock Home planning "
        "and response smoke checks."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
