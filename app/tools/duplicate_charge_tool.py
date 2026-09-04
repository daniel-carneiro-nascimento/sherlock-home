from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.duplicate_charge_analysis import (
    detect_duplicate_charges,
)
from app.tools.financial_tools import (
    FINANCIAL_CURRENCY,
    ToolArgumentError,
    _financial_evidence,
    _reject_unknown_arguments,
    _required_date,
)


def run_duplicate_charges(
    session: Session,
    arguments: dict[str, Any],
) -> object:
    _reject_unknown_arguments(
        arguments,
        allowed={
            "start_date",
            "end_date",
        },
    )

    result = detect_duplicate_charges(
        session,
        start_date=_required_date(
            arguments,
            "start_date",
        ),
        end_date=_required_date(
            arguments,
            "end_date",
        ),
    )

    return _financial_evidence(
        result,
        metadata={
            "duplicate_charge_policy": {
                "currency": (
                    FINANCIAL_CURRENCY
                ),
                "match_type": (
                    "exact"
                ),
                "minimum_occurrences": 2,
                "same_date_required": True,
                "same_merchant_required": True,
                "same_amount_required": True,
                "same_description_required": True,
                "fingerprint_used_for_matching": False,
            }
        },
    )
