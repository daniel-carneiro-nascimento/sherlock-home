from __future__ import annotations

from decimal import Decimal

import pytest

from app.tools import financial_tools
from app.tools.financial_tools import ToolArgumentError


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        ("0.10", Decimal("0.10")),
        (1, Decimal("1")),
        (0.1, Decimal("0.1")),
        (2.0, Decimal("2.0")),
        (Decimal("0.25"), Decimal("0.25")),
    ],
)
def test_optional_decimal_accepts_json_numeric_values(
    raw_value,
    expected,
):
    result = financial_tools._optional_decimal(
        {"value": raw_value},
        "value",
        Decimal("9.99"),
    )

    assert result == expected


def test_optional_decimal_still_rejects_boolean():
    with pytest.raises(
        ToolArgumentError,
        match="decimal value",
    ):
        financial_tools._optional_decimal(
            {"value": True},
            "value",
            Decimal("9.99"),
        )


def test_recurring_expenses_accepts_float_amount_tolerance(
    monkeypatch,
):
    captured = {}

    def fake_find(
        session,
        **kwargs,
    ):
        captured.update(kwargs)
        return {
            "start_date": kwargs["start_date"],
            "end_date": kwargs["end_date"],
            "candidates": [],
        }

    monkeypatch.setattr(
        financial_tools,
        "find_recurring_expenses",
        fake_find,
    )

    result = financial_tools.run_recurring_expenses(
        None,
        {
            "start_date": "2026-06-01",
            "end_date": "2026-08-01",
            "amount_tolerance": 0.1,
        },
    )

    assert captured["amount_tolerance"] == Decimal("0.1")
    assert (
        result["recurrence_policy"]["amount_tolerance"]
        == "0.1"
    )


def test_anomaly_detection_accepts_float_threshold_multiplier(
    monkeypatch,
):
    captured = {}

    def fake_detect(
        session,
        **kwargs,
    ):
        captured.update(kwargs)
        return {
            "start_date": "2026-06-01",
            "end_date": "2026-08-01",
            "anomalies": [],
        }

    monkeypatch.setattr(
        financial_tools,
        "detect_spending_anomalies",
        fake_detect,
    )

    result = financial_tools.run_spending_anomalies(
        None,
        {
            "start_date": "2026-06-01",
            "end_date": "2026-08-01",
            "threshold_multiplier": 2.0,
        },
    )

    assert (
        captured["threshold_multiplier"]
        == Decimal("2.0")
    )
    assert (
        result["anomaly_policy"]["threshold_multiplier"]
        == "2.0"
    )
