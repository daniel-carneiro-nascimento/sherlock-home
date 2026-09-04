from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

import pytest

from app.agents.financial_agent import AgentEvidence
from app.agents.ollama_responder import (
    OllamaFinancialResponder,
    RESPONDER_SYSTEM_PROMPT,
)
from app.tools import financial_tools
from app.tools.financial_tools import (
    ToolArgumentError,
)
from app.tools.registry import ToolRegistry
from app.tools.schemas import ToolExecutionResult


class FakeOllamaClient:
    def __init__(self, response: str = "ok"):
        self.response = response
        self.calls = []

    def chat(self, **kwargs) -> str:
        self.calls.append(kwargs)
        return self.response


def test_all_financial_tool_evidence_carries_brl(
    monkeypatch,
):
    monkeypatch.setattr(
        financial_tools,
        "get_monthly_spending",
        lambda session, **kwargs: {
            "total": Decimal("10.00"),
        },
    )

    result = financial_tools.run_monthly_spending(
        None,
        {
            "year": 2026,
            "month": 7,
        },
    )

    assert result["currency"] == "BRL"
    assert result["total"] == "10.00"


@pytest.mark.parametrize(
    ("start_date", "end_date", "expected"),
    [
        (
            date(2026, 6, 1),
            date(2026, 8, 1),
            2,
        ),
        (
            date(2026, 6, 15),
            date(2026, 8, 1),
            2,
        ),
        (
            date(2026, 6, 1),
            date(2026, 9, 1),
            3,
        ),
        (
            date(2026, 6, 30),
            date(2026, 9, 1),
            3,
        ),
    ],
)
def test_recurrence_policy_is_deterministic_by_calendar_span(
    start_date,
    end_date,
    expected,
):
    assert (
        financial_tools._recurrence_min_occurrences(
            start_date=start_date,
            end_date=end_date,
        )
        == expected
    )


def test_recurrence_min_occurrences_cannot_be_set_by_model():
    with pytest.raises(
        ToolArgumentError,
        match="min_occurrences",
    ):
        financial_tools.run_recurring_expenses(
            None,
            {
                "start_date": "2026-06-01",
                "end_date": "2026-08-01",
                "min_occurrences": 1,
            },
        )


def test_two_month_recurrence_uses_two_occurrences(
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
        },
    )

    assert captured["min_occurrences"] == 2
    assert (
        result["recurrence_policy"][
            "min_occurrences"
        ]
        == 2
    )
    assert (
        result["recurrence_policy"][
            "calendar_month_span"
        ]
        == 2
    )
    assert result["currency"] == "BRL"


def test_three_month_recurrence_uses_three_occurrences(
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
            "end_date": "2026-09-01",
        },
    )

    assert captured["min_occurrences"] == 3
    assert (
        result["recurrence_policy"][
            "min_occurrences"
        ]
        == 3
    )


def test_registry_does_not_expose_min_occurrences_to_model():
    tool = ToolRegistry().get(
        "find_recurring_expenses"
    )

    assert (
        "min_occurrences"
        not in tool.argument_names
    )

    assert (
        "model must not choose min_occurrences"
        in tool.description
    )


def test_anomaly_evidence_preserves_explanation_fields(
    monkeypatch,
):
    def fake_detect(
        session,
        **kwargs,
    ):
        return {
            "start_date": "2026-06-01",
            "end_date": "2026-08-01",
            "anomalies": [
                {
                    "transaction_id": 10,
                    "transaction_date": "2026-07-08",
                    "merchant": "CAFE DO BAIRRO",
                    "category": "food",
                    "amount": Decimal("84.90"),
                    "baseline_amount": Decimal("19.84"),
                    "threshold_amount": Decimal("39.68"),
                    "baseline_count": 5,
                    "match_basis": "merchant",
                }
            ],
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
        },
    )

    anomaly = result["anomalies"][0]

    assert result["currency"] == "BRL"
    assert anomaly["baseline_amount"] == "19.84"
    assert anomaly["threshold_amount"] == "39.68"
    assert anomaly["baseline_count"] == 5

    assert result["anomaly_policy"] == {
        "min_history": 3,
        "threshold_multiplier": "2.00",
        "explanation_fields": [
            "baseline_amount",
            "threshold_amount",
            "baseline_count",
        ],
    }


def test_responder_contract_uses_currency_and_anomaly_evidence():
    assert (
        "Never infer a currency"
        in RESPONDER_SYSTEM_PROMPT
    )
    assert (
        "baseline_amount"
        in RESPONDER_SYSTEM_PROMPT
    )
    assert (
        "threshold_amount"
        in RESPONDER_SYSTEM_PROMPT
    )
    assert (
        "baseline_count"
        in RESPONDER_SYSTEM_PROMPT
    )
    assert (
        "Never infer fraud"
        in RESPONDER_SYSTEM_PROMPT
    )


def test_responder_receives_brl_and_anomaly_explanation_fields():
    client = FakeOllamaClient()

    responder = OllamaFinancialResponder(
        client=client
    )

    evidence = AgentEvidence(
        user_message=(
            "Existem gastos anômalos?"
        ),
        tool_results=(
            ToolExecutionResult(
                tool_name=(
                    "detect_spending_anomalies"
                ),
                data={
                    "currency": "BRL",
                    "anomalies": [
                        {
                            "amount": "84.90",
                            "baseline_amount": "19.84",
                            "threshold_amount": "39.68",
                            "baseline_count": 5,
                        }
                    ],
                },
            ),
        ),
        answer_instruction=None,
    )

    responder.respond(evidence)

    payload = json.loads(
        client.calls[0]["messages"][1][
            "content"
        ]
    )

    data = payload[
        "tool_results"
    ][0]["data"]

    assert data["currency"] == "BRL"
    assert (
        data["anomalies"][0][
            "baseline_amount"
        ]
        == "19.84"
    )
    assert (
        data["anomalies"][0][
            "threshold_amount"
        ]
        == "39.68"
    )
    assert (
        data["anomalies"][0][
            "baseline_count"
        ]
        == 5
    )
