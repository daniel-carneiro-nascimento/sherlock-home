from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.category_rule import CategoryRuleModel
from app.models.merchant_alias import MerchantAliasModel


class PriorityConflictError(RuntimeError):
    pass


def _flush_or_priority_conflict(session: Session) -> None:
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise PriorityConflictError(
            "Priority is already in use."
        ) from exc


def list_category_rules(
    session: Session,
) -> list[CategoryRuleModel]:
    return list(
        session.scalars(
            select(CategoryRuleModel).order_by(
                CategoryRuleModel.priority,
                CategoryRuleModel.id,
            )
        ).all()
    )


def get_category_rule_by_public_id(
    session: Session,
    public_id: str,
) -> CategoryRuleModel | None:
    return session.scalar(
        select(CategoryRuleModel).where(
            CategoryRuleModel.public_id == public_id
        )
    )


def create_category_rule(
    session: Session,
    *,
    category: str,
    field: str,
    pattern: str,
    priority: int,
    enabled: bool,
) -> CategoryRuleModel:
    rule = CategoryRuleModel(
        category=category,
        field=field,
        pattern=pattern,
        priority=priority,
        enabled=enabled,
    )

    session.add(rule)
    _flush_or_priority_conflict(session)
    session.refresh(rule)

    return rule


def update_category_rule(
    session: Session,
    rule: CategoryRuleModel,
    *,
    category: str,
    field: str,
    pattern: str,
    priority: int,
    enabled: bool,
) -> CategoryRuleModel:
    rule.category = category
    rule.field = field
    rule.pattern = pattern
    rule.priority = priority
    rule.enabled = enabled

    _flush_or_priority_conflict(session)
    session.refresh(rule)

    return rule


def set_category_rule_enabled(
    session: Session,
    rule: CategoryRuleModel,
    *,
    enabled: bool,
) -> CategoryRuleModel:
    rule.enabled = enabled
    session.flush()
    session.refresh(rule)

    return rule


def list_merchant_aliases(
    session: Session,
) -> list[MerchantAliasModel]:
    return list(
        session.scalars(
            select(MerchantAliasModel).order_by(
                MerchantAliasModel.priority,
                MerchantAliasModel.id,
            )
        ).all()
    )


def get_merchant_alias_by_public_id(
    session: Session,
    public_id: str,
) -> MerchantAliasModel | None:
    return session.scalar(
        select(MerchantAliasModel).where(
            MerchantAliasModel.public_id == public_id
        )
    )


def create_merchant_alias(
    session: Session,
    *,
    canonical_name: str,
    pattern: str,
    priority: int,
    enabled: bool,
) -> MerchantAliasModel:
    alias = MerchantAliasModel(
        canonical_name=canonical_name,
        pattern=pattern,
        priority=priority,
        enabled=enabled,
    )

    session.add(alias)
    _flush_or_priority_conflict(session)
    session.refresh(alias)

    return alias


def update_merchant_alias(
    session: Session,
    alias: MerchantAliasModel,
    *,
    canonical_name: str,
    pattern: str,
    priority: int,
    enabled: bool,
) -> MerchantAliasModel:
    alias.canonical_name = canonical_name
    alias.pattern = pattern
    alias.priority = priority
    alias.enabled = enabled

    _flush_or_priority_conflict(session)
    session.refresh(alias)

    return alias


def set_merchant_alias_enabled(
    session: Session,
    alias: MerchantAliasModel,
    *,
    enabled: bool,
) -> MerchantAliasModel:
    alias.enabled = enabled
    session.flush()
    session.refresh(alias)

    return alias
