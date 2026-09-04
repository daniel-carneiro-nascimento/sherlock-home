from scripts.validate_financial_capabilities import (
    SCENARIOS,
)


def test_duplicate_charge_validation_scenario_exists():
    scenario = next(
        scenario
        for scenario in SCENARIOS
        if scenario.name
        == "duplicate_charges"
    )

    assert scenario.expected_tools == (
        "detect_duplicate_charges",
    )


def test_suspicious_spending_requires_both_detectors():
    scenario = next(
        scenario
        for scenario in SCENARIOS
        if scenario.name
        == "suspicious_spending"
    )

    assert scenario.expected_tools == (
        "detect_spending_anomalies",
        "detect_duplicate_charges",
    )
