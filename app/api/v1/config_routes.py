from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.api.v1.dependencies import (
    get_db_session,
    require_admin,
    require_csrf,
)
from app.api.v1.schemas.category_rules import (
    CategoryRuleCreate,
    CategoryRuleEnabledUpdate,
    CategoryRuleResponse,
    CategoryRuleUpdate,
)
from app.api.v1.schemas.merchant_aliases import (
    MerchantAliasCreate,
    MerchantAliasEnabledUpdate,
    MerchantAliasResponse,
    MerchantAliasUpdate,
)
from app.core.public_ids import (
    is_category_rule_id,
    is_merchant_alias_id,
)
from app.models.user import User
from app.services.config_audit import record_config_change
from app.services.config_management import (
    PriorityConflictError,
    create_category_rule,
    create_merchant_alias,
    get_category_rule_by_public_id,
    get_merchant_alias_by_public_id,
    list_category_rules,
    list_merchant_aliases,
    set_category_rule_enabled,
    set_merchant_alias_enabled,
    update_category_rule,
    update_merchant_alias,
)


router = APIRouter(
    prefix="/config",
    tags=["configuration"],
)


def _priority_conflict(
    exc: PriorityConflictError,
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=str(exc),
    )


def _get_category_rule_or_404(
    db: Session,
    rule_id: str,
):
    if not is_category_rule_id(rule_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category rule not found.",
        )

    rule = get_category_rule_by_public_id(
        db,
        rule_id,
    )

    if rule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category rule not found.",
        )

    return rule


def _get_merchant_alias_or_404(
    db: Session,
    alias_id: str,
):
    if not is_merchant_alias_id(alias_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant alias not found.",
        )

    alias = get_merchant_alias_by_public_id(
        db,
        alias_id,
    )

    if alias is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant alias not found.",
        )

    return alias


def _commit_audited_change(
    db: Session,
    *,
    actor_user_id: int,
    resource_type: str,
    action: str,
    resource_public_id: str,
) -> None:
    """
    Commit the resource mutation and audit row in one DB transaction.
    """
    try:
        record_config_change(
            db,
            actor_user_id=actor_user_id,
            resource_type=resource_type,
            action=action,
            resource_public_id=resource_public_id,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise


@router.get(
    "/category-rules",
    response_model=list[CategoryRuleResponse],
)
def get_category_rules(
    db: Session = Depends(get_db_session),
    _: User = Depends(require_admin),
):
    return list_category_rules(db)


@router.post(
    "/category-rules",
    response_model=CategoryRuleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
def post_category_rule(
    payload: CategoryRuleCreate,
    db: Session = Depends(get_db_session),
    admin: User = Depends(require_admin),
):
    try:
        rule = create_category_rule(
            db,
            category=payload.category.value,
            field=payload.field.value,
            pattern=payload.pattern,
            priority=payload.priority,
            enabled=payload.enabled,
        )
    except PriorityConflictError as exc:
        raise _priority_conflict(exc) from exc

    _commit_audited_change(
        db,
        actor_user_id=admin.id,
        resource_type="category_rule",
        action="create",
        resource_public_id=rule.public_id,
    )

    return rule


@router.get(
    "/category-rules/{rule_id}",
    response_model=CategoryRuleResponse,
)
def get_category_rule(
    rule_id: str,
    db: Session = Depends(get_db_session),
    _: User = Depends(require_admin),
):
    return _get_category_rule_or_404(
        db,
        rule_id,
    )


@router.put(
    "/category-rules/{rule_id}",
    response_model=CategoryRuleResponse,
    dependencies=[Depends(require_csrf)],
)
def put_category_rule(
    rule_id: str,
    payload: CategoryRuleUpdate,
    db: Session = Depends(get_db_session),
    admin: User = Depends(require_admin),
):
    rule = _get_category_rule_or_404(
        db,
        rule_id,
    )

    try:
        rule = update_category_rule(
            db,
            rule,
            category=payload.category.value,
            field=payload.field.value,
            pattern=payload.pattern,
            priority=payload.priority,
            enabled=payload.enabled,
        )
    except PriorityConflictError as exc:
        raise _priority_conflict(exc) from exc

    _commit_audited_change(
        db,
        actor_user_id=admin.id,
        resource_type="category_rule",
        action="update",
        resource_public_id=rule.public_id,
    )

    return rule


@router.patch(
    "/category-rules/{rule_id}/enabled",
    response_model=CategoryRuleResponse,
    dependencies=[Depends(require_csrf)],
)
def patch_category_rule_enabled(
    rule_id: str,
    payload: CategoryRuleEnabledUpdate,
    db: Session = Depends(get_db_session),
    admin: User = Depends(require_admin),
):
    rule = _get_category_rule_or_404(
        db,
        rule_id,
    )

    rule = set_category_rule_enabled(
        db,
        rule,
        enabled=payload.enabled,
    )

    action = (
        "enable"
        if payload.enabled
        else "disable"
    )

    _commit_audited_change(
        db,
        actor_user_id=admin.id,
        resource_type="category_rule",
        action=action,
        resource_public_id=rule.public_id,
    )

    return rule


@router.delete(
    "/category-rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_csrf)],
)
def delete_category_rule(
    rule_id: str,
    db: Session = Depends(get_db_session),
    admin: User = Depends(require_admin),
) -> Response:
    rule = _get_category_rule_or_404(
        db,
        rule_id,
    )
    public_id = rule.public_id

    db.delete(rule)
    db.flush()

    _commit_audited_change(
        db,
        actor_user_id=admin.id,
        resource_type="category_rule",
        action="delete",
        resource_public_id=public_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.get(
    "/merchant-aliases",
    response_model=list[MerchantAliasResponse],
)
def get_merchant_aliases(
    db: Session = Depends(get_db_session),
    _: User = Depends(require_admin),
):
    return list_merchant_aliases(db)


@router.post(
    "/merchant-aliases",
    response_model=MerchantAliasResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
def post_merchant_alias(
    payload: MerchantAliasCreate,
    db: Session = Depends(get_db_session),
    admin: User = Depends(require_admin),
):
    try:
        alias = create_merchant_alias(
            db,
            canonical_name=payload.canonical_name,
            pattern=payload.pattern,
            priority=payload.priority,
            enabled=payload.enabled,
        )
    except PriorityConflictError as exc:
        raise _priority_conflict(exc) from exc

    _commit_audited_change(
        db,
        actor_user_id=admin.id,
        resource_type="merchant_alias",
        action="create",
        resource_public_id=alias.public_id,
    )

    return alias


@router.get(
    "/merchant-aliases/{alias_id}",
    response_model=MerchantAliasResponse,
)
def get_merchant_alias(
    alias_id: str,
    db: Session = Depends(get_db_session),
    _: User = Depends(require_admin),
):
    return _get_merchant_alias_or_404(
        db,
        alias_id,
    )


@router.put(
    "/merchant-aliases/{alias_id}",
    response_model=MerchantAliasResponse,
    dependencies=[Depends(require_csrf)],
)
def put_merchant_alias(
    alias_id: str,
    payload: MerchantAliasUpdate,
    db: Session = Depends(get_db_session),
    admin: User = Depends(require_admin),
):
    alias = _get_merchant_alias_or_404(
        db,
        alias_id,
    )

    try:
        alias = update_merchant_alias(
            db,
            alias,
            canonical_name=payload.canonical_name,
            pattern=payload.pattern,
            priority=payload.priority,
            enabled=payload.enabled,
        )
    except PriorityConflictError as exc:
        raise _priority_conflict(exc) from exc

    _commit_audited_change(
        db,
        actor_user_id=admin.id,
        resource_type="merchant_alias",
        action="update",
        resource_public_id=alias.public_id,
    )

    return alias


@router.patch(
    "/merchant-aliases/{alias_id}/enabled",
    response_model=MerchantAliasResponse,
    dependencies=[Depends(require_csrf)],
)
def patch_merchant_alias_enabled(
    alias_id: str,
    payload: MerchantAliasEnabledUpdate,
    db: Session = Depends(get_db_session),
    admin: User = Depends(require_admin),
):
    alias = _get_merchant_alias_or_404(
        db,
        alias_id,
    )

    alias = set_merchant_alias_enabled(
        db,
        alias,
        enabled=payload.enabled,
    )

    action = (
        "enable"
        if payload.enabled
        else "disable"
    )

    _commit_audited_change(
        db,
        actor_user_id=admin.id,
        resource_type="merchant_alias",
        action=action,
        resource_public_id=alias.public_id,
    )

    return alias


@router.delete(
    "/merchant-aliases/{alias_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_csrf)],
)
def delete_merchant_alias(
    alias_id: str,
    db: Session = Depends(get_db_session),
    admin: User = Depends(require_admin),
) -> Response:
    alias = _get_merchant_alias_or_404(
        db,
        alias_id,
    )
    public_id = alias.public_id

    db.delete(alias)
    db.flush()

    _commit_audited_change(
        db,
        actor_user_id=admin.id,
        resource_type="merchant_alias",
        action="delete",
        resource_public_id=public_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )
