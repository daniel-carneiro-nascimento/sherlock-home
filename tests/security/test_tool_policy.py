from app.core.tool_policy import (
    ToolPermission,
    validate_tool,
    validate_tool_permission,
)


def test_approved_tool():
    assert validate_tool(
        "get_monthly_spending"
    ) is None


def test_unapproved_tool():
    violation = validate_tool(
        "delete_all_financial_data"
    )

    assert violation is not None
    assert violation.rule_id == "SH-TOOL-001"


def test_allowed_tool_permission():
    violation = validate_tool_permission(
        "get_monthly_spending",
        {
            ToolPermission.READ,
            ToolPermission.ANALYZE,
        },
    )

    assert violation is None


def test_disallowed_tool_permission():
    violation = validate_tool_permission(
        "compare_months",
        {
            ToolPermission.READ,
        },
    )

    assert violation is not None
    assert violation.rule_id == "SH-TOOL-002"


def test_unknown_tool_permission_check():
    violation = validate_tool_permission(
        "send_financial_data_to_cloud",
        {
            ToolPermission.READ,
            ToolPermission.ANALYZE,
            ToolPermission.WRITE,
            ToolPermission.ADMIN,
        },
    )

    assert violation is not None
    assert violation.rule_id == "SH-TOOL-001"
