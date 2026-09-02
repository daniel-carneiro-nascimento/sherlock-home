import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.merchant_alias import (
    MerchantAliasModel,
)
from app.rules.merchant_aliases import (
    MerchantAliasRule,
)


def load_merchant_aliases_from_db(
    session: Session,
) -> tuple[MerchantAliasRule, ...]:
    rows = session.scalars(
        select(MerchantAliasModel)
        .where(
            MerchantAliasModel.enabled.is_(True)
        )
        .order_by(
            MerchantAliasModel.priority
        )
    ).all()

    return tuple(
        MerchantAliasRule(
            canonical_name=row.canonical_name,
            pattern=re.compile(
                row.pattern,
                re.IGNORECASE,
            ),
            priority=row.priority,
        )
        for row in rows
    )
