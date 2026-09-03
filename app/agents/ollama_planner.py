from __future__ import annotations

import json
from dataclasses import dataclass

from app.agents.ollama_runtime import (
    OllamaClient,
)
from app.agents.tool_planning import (
    ToolPlan,
    build_tool_planning_context,
    parse_tool_plan,
)
from app.tools.registry import (
    ToolRegistry,
)


PLANNER_SYSTEM_PROMPT = """
You are the tool-planning component of Sherlock Home.

Your only job is to decide which approved deterministic financial tools are
needed to answer the user's message.

Rules:
- Output JSON only.
- Never answer the user's financial question directly.
- Never invent a tool.
- Never request SQL, shell commands, Python execution, files, network access,
  credentials, or database access.
- Use only tools listed in the supplied tool context.
- Request only the minimum tools needed.
- Tool arguments must follow the supplied tool metadata.
- The deterministic dispatcher and security policy are authoritative.
- If no tool is required, return an empty calls list.
- answer_instruction may briefly state how the final answer should use the
  resulting evidence.
- For compare_monthly_spending, base is the month being evaluated and
  comparison is the reference month.
- When the user says "compare A and B" without specifying direction, use the
  later month as base/target and the earlier month as comparison/reference.
- Example: "compare June and July 2026" means July relative to June:
  base_year=2026, base_month=7, comparison_year=2026, comparison_month=6.
""".strip()


@dataclass
class OllamaFinancialPlanner:
    client: OllamaClient
    registry: ToolRegistry

    def plan(
        self,
        user_message: str,
    ) -> ToolPlan:
        if not isinstance(
            user_message,
            str,
        ):
            raise TypeError(
                "user_message must be a string"
            )

        user_message = (
            user_message.strip()
        )

        if not user_message:
            raise ValueError(
                "user_message must not be empty"
            )

        planning_context = (
            build_tool_planning_context(
                self.registry
            )
        )

        prompt_payload = {
            "tool_context": (
                planning_context
            ),
            "user_message": (
                user_message
            ),
            "required_output_example": {
                "calls": [
                    {
                        "name": (
                            "get_monthly_spending"
                        ),
                        "arguments": {
                            "year": 2026,
                            "month": 9,
                        },
                    }
                ],
                "answer_instruction": (
                    "Use the returned "
                    "evidence only."
                ),
            },
            "comparison_example": {
                "user_message": (
                    "Compare June and "
                    "July 2026."
                ),
                "call": {
                    "name": (
                        "compare_monthly_spending"
                    ),
                    "arguments": {
                        "base_year": 2026,
                        "base_month": 7,
                        "comparison_year": 2026,
                        "comparison_month": 6,
                    },
                },
                "meaning": (
                    "Evaluate July relative "
                    "to June."
                ),
            },
        }

        raw_plan = self.client.chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        PLANNER_SYSTEM_PROMPT
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        prompt_payload,
                        ensure_ascii=False,
                    ),
                },
            ],
            json_mode=True,
            temperature=0.0,
        )

        return parse_tool_plan(
            raw_plan,
            registry=self.registry,
        )
