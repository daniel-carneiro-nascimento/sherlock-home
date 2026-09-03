from dataclasses import dataclass
from decimal import Decimal

import pytest

from app.core.runtime_state import RuntimeCompromisedError, runtime_security_state
from app.core.security_enforcer import SecurityPolicyError
from app.core.tool_policy import ToolPermission
from app.tools.dispatcher import ToolDispatcher
from app.tools.registry import RegisteredTool, ToolRegistry
from app.tools.schemas import ToolCall


@dataclass(frozen=True)
class FakeResult:
    total: Decimal


def fake_read_handler(session, arguments):
    return FakeResult(total=Decimal(arguments["value"]))


def build_dispatcher(permission=ToolPermission.READ):
    return ToolDispatcher(
        ToolRegistry({
            "fake_tool": RegisteredTool(
                "fake_tool", "synthetic", permission,
                fake_read_handler, ("value",),
            )
        })
    )


def test_dispatcher_serializes_decimal_without_float_conversion(monkeypatch):
    from app.core import tool_policy
    monkeypatch.setitem(
        tool_policy.APPROVED_TOOLS,
        "fake_tool",
        tool_policy.ToolDefinition("fake_tool", ToolPermission.READ),
    )

    result = build_dispatcher().execute(
        None,
        ToolCall("fake_tool", {"value": "10.25"}),
        allowed_permissions={ToolPermission.READ},
    )
    assert result.data["total"] == "10.25"


def test_dispatcher_enforces_permission(monkeypatch):
    from app.core import tool_policy
    monkeypatch.setitem(
        tool_policy.APPROVED_TOOLS,
        "fake_tool",
        tool_policy.ToolDefinition("fake_tool", ToolPermission.ANALYZE),
    )

    with pytest.raises(SecurityPolicyError):
        build_dispatcher(ToolPermission.ANALYZE).execute(
            None,
            ToolCall("fake_tool", {"value": "10.00"}),
            allowed_permissions={ToolPermission.READ},
        )


def test_dispatcher_rejects_unregistered_tool():
    with pytest.raises(SecurityPolicyError):
        ToolDispatcher(ToolRegistry({})).execute(
            None,
            ToolCall("execute_arbitrary_sql", {}),
            allowed_permissions={ToolPermission.READ, ToolPermission.ANALYZE},
        )


def test_dispatcher_fails_closed_when_runtime_compromised(monkeypatch):
    from app.core import tool_policy
    monkeypatch.setitem(
        tool_policy.APPROVED_TOOLS,
        "fake_tool",
        tool_policy.ToolDefinition("fake_tool", ToolPermission.READ),
    )

    previous = (
        runtime_security_state.compromised,
        runtime_security_state.reason,
        runtime_security_state.rule_id,
    )
    runtime_security_state.compromised = True
    runtime_security_state.reason = "synthetic_test"
    runtime_security_state.rule_id = "SH-TEST"

    try:
        with pytest.raises(RuntimeCompromisedError):
            build_dispatcher().execute(
                None,
                ToolCall("fake_tool", {"value": "10.00"}),
                allowed_permissions={ToolPermission.READ},
            )
    finally:
        (
            runtime_security_state.compromised,
            runtime_security_state.reason,
            runtime_security_state.rule_id,
        ) = previous
