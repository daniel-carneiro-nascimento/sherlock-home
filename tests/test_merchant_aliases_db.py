from sqlalchemy.orm import Session

from app.models.merchant_alias import (
    MerchantAliasModel,
)
from app.services.merchant_aliases import (
    load_merchant_aliases_from_db,
)


def test_merchant_alias_can_be_loaded_from_db(
    db_session: Session,
):
    db_session.add(
        MerchantAliasModel(
            canonical_name="SYNTHETIC MARKET",
            pattern=(
                r"^SYNTHETIC MARKET"
                r"(?:\s+\*\d+)?$"
            ),
            priority=10,
            enabled=True,
        )
    )
    db_session.commit()

    rules = load_merchant_aliases_from_db(
        db_session
    )

    assert len(rules) == 1
    assert (
        rules[0].canonical_name
        == "SYNTHETIC MARKET"
    )
    assert rules[0].priority == 10
