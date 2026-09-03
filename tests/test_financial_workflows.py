from datetime import date

from app.agents.financial_workflows import spending_reduction_workflow


def test_spending_reduction_workflow_collects_four_evidence_sources():
    plan = spending_reduction_workflow(today=date(2026, 9, 3))
    assert [call.name for call in plan.calls] == [
        "get_monthly_spending",
        "get_category_spending",
        "compare_monthly_spending",
        "find_recurring_expenses",
    ]


def test_spending_reduction_workflow_uses_current_month():
    plan = spending_reduction_workflow(today=date(2026, 9, 3))
    assert plan.calls[0].arguments == {"year": 2026, "month": 9}


def test_spending_reduction_workflow_compares_previous_month():
    plan = spending_reduction_workflow(today=date(2026, 9, 3))
    assert plan.calls[2].arguments == {
        "base_year": 2026,
        "base_month": 9,
        "comparison_year": 2026,
        "comparison_month": 8,
    }


def test_spending_reduction_workflow_handles_january_boundary():
    plan = spending_reduction_workflow(today=date(2027, 1, 5))
    assert plan.calls[2].arguments["comparison_year"] == 2026
    assert plan.calls[2].arguments["comparison_month"] == 12


def test_spending_reduction_workflow_uses_bounded_recurring_window():
    plan = spending_reduction_workflow(today=date(2026, 9, 3))
    assert plan.calls[3].arguments["start_date"] == "2026-06-01"
    assert plan.calls[3].arguments["end_date"] == "2026-10-01"
