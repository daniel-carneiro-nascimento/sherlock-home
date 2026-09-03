from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.tools.registry import ToolRegistry
from app.tools.schemas import ToolCall


class ToolPlanError(ValueError):
    pass


MAX_PLAN_CALLS = 8


@dataclass(frozen=True)
class ToolPlan:
    calls: tuple[ToolCall, ...]
    answer_instruction: str | None = None


def parse_tool_plan(raw: str, *, registry: ToolRegistry) -> ToolPlan:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ToolPlanError("tool plan must be valid JSON") from exc

    if not isinstance(payload, dict):
        raise ToolPlanError("tool plan must be a JSON object")

    if set(payload) - {"calls", "answer_instruction"}:
        raise ToolPlanError("tool plan contains unknown top-level fields")

    calls_payload = payload.get("calls")
    if not isinstance(calls_payload, list):
        raise ToolPlanError("calls must be a list")
    if len(calls_payload) > MAX_PLAN_CALLS:
        raise ToolPlanError("tool plan exceeds maximum call count")

    known_tools = set(registry.names())
    calls: list[ToolCall] = []

    for item in calls_payload:
        if not isinstance(item, dict):
            raise ToolPlanError("each tool call must be an object")
        if set(item) != {"name", "arguments"}:
            raise ToolPlanError("tool call must contain only name and arguments")

        name = item["name"]
        arguments = item["arguments"]

        if not isinstance(name, str):
            raise ToolPlanError("tool name must be a string")
        if name not in known_tools:
            raise ToolPlanError("tool plan requested an unregistered tool")
        if not isinstance(arguments, dict):
            raise ToolPlanError("tool arguments must be an object")

        calls.append(ToolCall(name=name, arguments=dict(arguments)))

    answer_instruction = payload.get("answer_instruction")
    if answer_instruction is not None and not isinstance(answer_instruction, str):
        raise ToolPlanError("answer_instruction must be a string or null")

    return ToolPlan(calls=tuple(calls), answer_instruction=answer_instruction)


def build_tool_planning_context(registry: ToolRegistry) -> dict[str, Any]:
    return {
        "tools": registry.describe_for_model(),
        "planning_contract": {
            "format": "json",
            "top_level_fields": ["calls", "answer_instruction"],
            "max_calls": MAX_PLAN_CALLS,
            "tool_call_fields": ["name", "arguments"],
        },
    }
