from __future__ import annotations

import argparse
import sys

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.agents.chat_service import build_financial_chat_service
from app.agents.ollama_runtime import OllamaRuntimeError
from app.agents.tool_planning import ToolPlanError
from app.db.database import SessionLocal


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run one real Sherlock Home financial chat against the configured "
            "local PostgreSQL database and approved local Ollama runtime."
        )
    )
    parser.add_argument(
        "question",
        help=(
            "Financial question to send through the real Sherlock Home agent "
            "pipeline. Prefer an explicit month/date for the first end-to-end run."
        ),
    )
    parser.add_argument(
        "--hide-tools",
        action="store_true",
        help="Do not print the names of deterministic tools used by the agent.",
    )
    return parser


def run_chat(question: str, *, show_tools: bool = True) -> int:
    question = question.strip()

    if not question:
        print("ERROR: question must not be empty.", file=sys.stderr)
        return 2

    try:
        service = build_financial_chat_service()

        with SessionLocal() as session:
            # Connectivity-only preflight. Does not read household financial rows.
            session.execute(text("SELECT 1"))

            result = service.ask(
                session,
                user_message=question,
            )

    except SQLAlchemyError as exc:
        print("ERROR: PostgreSQL operation failed.", file=sys.stderr)
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    except (
        OllamaRuntimeError,
        ToolPlanError,
        ValueError,
        RuntimeError,
        KeyError,
    ) as exc:
        print("ERROR: Sherlock Home agent execution failed.", file=sys.stderr)
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print()
    print("Sherlock Home")
    print("-------------")

    if show_tools:
        if result.tools_used:
            print("Tools used: " + ", ".join(result.tools_used))
        else:
            print("Tools used: none")
        print()

    print(result.answer)
    print()

    return 0


def main() -> int:
    args = build_parser().parse_args()
    return run_chat(
        args.question,
        show_tools=not args.hide_tools,
    )


if __name__ == "__main__":
    sys.exit(main())
