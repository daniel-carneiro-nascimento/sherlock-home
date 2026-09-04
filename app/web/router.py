from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    Form,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
    Response,
)
from fastapi.templating import (
    Jinja2Templates,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.dependencies import (
    AuthContext,
    get_db_session,
    require_auth_context,
)
from app.api.v1.security import (
    CSRF_COOKIE_HTTPONLY,
    CSRF_COOKIE_NAME,
    CSRF_COOKIE_SAMESITE,
    CSRF_COOKIE_SECURE,
    SESSION_COOKIE_HTTPONLY,
    SESSION_COOKIE_NAME,
    SESSION_COOKIE_PATH,
    SESSION_COOKIE_SAMESITE,
    SESSION_COOKIE_SECURE,
)
from app.models.transaction import Transaction
from app.models.user import User
from app.services.auth import (
    SESSION_TTL,
    create_session,
    find_user_by_username,
    record_login_failure,
    record_login_success,
    revoke_session,
    verify_csrf,
    verify_password,
    verify_unknown_user_password,
)
from app.web.charts import (
    category_chart_svg,
    comparison_chart_svg,
)
from app.web.dashboard import (
    build_dashboard,
)
from app.web.preferences import (
    PresentationPreferences,
    load_preferences,
)

WEB_ROOT = Path(__file__).resolve().parent
templates = Jinja2Templates(
    directory=str(
        WEB_ROOT / "templates"
    )
)

router = APIRouter(
    prefix="/web",
    tags=["web"],
)

THEME_COOKIE = "sherlock_theme"
PALETTE_COOKIE = "sherlock_palette"
LAYOUT_COOKIE = "sherlock_layout"


def _preferences(
    theme: str | None,
    palette: str | None,
    layout: str | None,
) -> PresentationPreferences:
    return load_preferences(
        theme=theme,
        palette=palette,
        layout=layout,
    )


def _money(value: Decimal) -> str:
    negative = value < 0
    number = abs(value)
    rendered = (
        f"{number:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
    prefix = "-R$" if negative else "R$"
    return f"{prefix} {rendered}"


templates.env.filters["money"] = _money


def _set_auth_cookies(
    response: Response,
    *,
    session_token: str,
    csrf_token: str,
) -> None:
    max_age = int(
        SESSION_TTL.total_seconds()
    )

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=max_age,
        expires=max_age,
        path=SESSION_COOKIE_PATH,
        secure=SESSION_COOKIE_SECURE,
        httponly=(
            SESSION_COOKIE_HTTPONLY
        ),
        samesite=(
            SESSION_COOKIE_SAMESITE
        ),
    )

    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=max_age,
        expires=max_age,
        path=SESSION_COOKIE_PATH,
        secure=CSRF_COOKIE_SECURE,
        httponly=(
            CSRF_COOKIE_HTTPONLY
        ),
        samesite=(
            CSRF_COOKIE_SAMESITE
        ),
    )


def _clear_auth_cookies(
    response: Response,
) -> None:
    response.delete_cookie(
        SESSION_COOKIE_NAME,
        path=SESSION_COOKIE_PATH,
        secure=SESSION_COOKIE_SECURE,
        httponly=(
            SESSION_COOKIE_HTTPONLY
        ),
        samesite=(
            SESSION_COOKIE_SAMESITE
        ),
    )

    response.delete_cookie(
        CSRF_COOKIE_NAME,
        path=SESSION_COOKIE_PATH,
        secure=CSRF_COOKIE_SECURE,
        httponly=(
            CSRF_COOKIE_HTTPONLY
        ),
        samesite=(
            CSRF_COOKIE_SAMESITE
        ),
    )


def _require_form_csrf(
    auth: AuthContext,
    csrf_cookie: str | None,
    csrf_form: str,
) -> None:
    if (
        not csrf_cookie
        or not csrf_form
        or csrf_cookie != csrf_form
        or not verify_csrf(
            auth.session,
            csrf_form,
        )
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "CSRF validation failed."
            ),
        )


def _latest_month_totals(
    db: Session,
) -> tuple[Decimal, Decimal]:
    latest = db.scalar(
        select(func.max(Transaction.date))
    )

    if latest is None:
        return (
            Decimal("0.00"),
            Decimal("0.00"),
        )

    if latest.month == 1:
        previous_year = latest.year - 1
        previous_month = 12
    else:
        previous_year = latest.year
        previous_month = (
            latest.month - 1
        )

    from app.services.financial_analysis import (
        get_monthly_spending,
    )

    current = get_monthly_spending(
        db,
        year=latest.year,
        month=latest.month,
    )

    previous = get_monthly_spending(
        db,
        year=previous_year,
        month=previous_month,
    )

    return current.total, previous.total


@router.get(
    "",
    include_in_schema=False,
)
def web_root() -> RedirectResponse:
    return RedirectResponse(
        url="/web/dashboard",
        status_code=303,
    )


@router.get(
    "/login",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def login_page(
    request: Request,
    theme: str | None = Cookie(
        default=None,
        alias=THEME_COOKIE,
    ),
) -> HTMLResponse:
    preferences = _preferences(
        theme,
        None,
        None,
    )

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "preferences": preferences,
            "error": None,
        },
    )


@router.post(
    "/login",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(
        get_db_session
    ),
) -> Response:
    normalized = username.strip()

    if not normalized:
        preferences = (
            PresentationPreferences()
        )
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "preferences": preferences,
                "error": (
                    "Informe seu usuário."
                ),
            },
            status_code=400,
        )

    user = find_user_by_username(
        db,
        normalized,
    )

    if user is None:
        verify_unknown_user_password(
            password
        )
        preferences = (
            PresentationPreferences()
        )
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "preferences": preferences,
                "error": (
                    "Credenciais inválidas."
                ),
            },
            status_code=401,
        )

    if (
        not user.is_active
        or not verify_password(
            user.password_hash,
            password,
        )
    ):
        record_login_failure(
            db,
            user,
        )
        preferences = (
            PresentationPreferences()
        )
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "preferences": preferences,
                "error": (
                    "Credenciais inválidas."
                ),
            },
            status_code=401,
        )

    record_login_success(
        db,
        user,
        password=password,
    )

    created = create_session(
        db,
        user_id=user.id,
    )

    response = RedirectResponse(
        url="/web/dashboard",
        status_code=303,
    )

    _set_auth_cookies(
        response,
        session_token=(
            created.session_token
        ),
        csrf_token=(
            created.csrf_token
        ),
    )

    response.headers[
        "Cache-Control"
    ] = "no-store"

    return response


@router.get(
    "/dashboard",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def dashboard_page(
    request: Request,
    auth: AuthContext = Depends(
        require_auth_context
    ),
    db: Session = Depends(
        get_db_session
    ),
    theme: str | None = Cookie(
        default=None,
        alias=THEME_COOKIE,
    ),
    palette: str | None = Cookie(
        default=None,
        alias=PALETTE_COOKIE,
    ),
    layout: str | None = Cookie(
        default=None,
        alias=LAYOUT_COOKIE,
    ),
    csrf_cookie: str | None = Cookie(
        default=None,
        alias=CSRF_COOKIE_NAME,
    ),
) -> HTMLResponse:
    preferences = _preferences(
        theme,
        palette,
        layout,
    )

    view = build_dashboard(db)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "auth": auth,
            "view": view,
            "preferences": preferences,
            "csrf_token": (
                csrf_cookie or ""
            ),
            "single_household": True,
        },
        headers={
            "Cache-Control": "no-store"
        },
    )


@router.get(
    "/settings",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def settings_page(
    request: Request,
    auth: AuthContext = Depends(
        require_auth_context
    ),
    theme: str | None = Cookie(
        default=None,
        alias=THEME_COOKIE,
    ),
    palette: str | None = Cookie(
        default=None,
        alias=PALETTE_COOKIE,
    ),
    layout: str | None = Cookie(
        default=None,
        alias=LAYOUT_COOKIE,
    ),
    csrf_cookie: str | None = Cookie(
        default=None,
        alias=CSRF_COOKIE_NAME,
    ),
) -> HTMLResponse:
    preferences = _preferences(
        theme,
        palette,
        layout,
    )

    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={
            "auth": auth,
            "preferences": preferences,
            "csrf_token": (
                csrf_cookie or ""
            ),
        },
        headers={
            "Cache-Control": "no-store"
        },
    )


@router.post(
    "/settings/presentation",
    include_in_schema=False,
)
def update_presentation(
    auth: AuthContext = Depends(
        require_auth_context
    ),
    theme: str = Form("light"),
    palette: str = Form("standard"),
    layout: str = Form("balanced"),
    csrf_token: str = Form(...),
    csrf_cookie: str | None = Cookie(
        default=None,
        alias=CSRF_COOKIE_NAME,
    ),
) -> RedirectResponse:
    _require_form_csrf(
        auth,
        csrf_cookie,
        csrf_token,
    )

    preferences = load_preferences(
        theme=theme,
        palette=palette,
        layout=layout,
    )

    response = RedirectResponse(
        url="/web/settings",
        status_code=303,
    )

    response.set_cookie(
        THEME_COOKIE,
        preferences.theme,
        max_age=31536000,
        secure=True,
        httponly=True,
        samesite="strict",
    )
    response.set_cookie(
        PALETTE_COOKIE,
        preferences.palette,
        max_age=31536000,
        secure=True,
        httponly=True,
        samesite="strict",
    )
    response.set_cookie(
        LAYOUT_COOKIE,
        preferences.layout,
        max_age=31536000,
        secure=True,
        httponly=True,
        samesite="strict",
    )

    return response


@router.post(
    "/logout",
    include_in_schema=False,
)
def logout(
    auth: AuthContext = Depends(
        require_auth_context
    ),
    csrf_token: str = Form(...),
    csrf_cookie: str | None = Cookie(
        default=None,
        alias=CSRF_COOKIE_NAME,
    ),
    db: Session = Depends(
        get_db_session
    ),
) -> RedirectResponse:
    _require_form_csrf(
        auth,
        csrf_cookie,
        csrf_token,
    )

    revoke_session(
        db,
        auth.session,
    )

    response = RedirectResponse(
        url="/web/login",
        status_code=303,
    )

    _clear_auth_cookies(
        response
    )

    return response


@router.get(
    "/charts/categories.svg",
    include_in_schema=False,
)
def categories_chart(
    auth: AuthContext = Depends(
        require_auth_context
    ),
    db: Session = Depends(
        get_db_session
    ),
    theme: str | None = Cookie(
        default=None,
        alias=THEME_COOKIE,
    ),
    palette: str | None = Cookie(
        default=None,
        alias=PALETTE_COOKIE,
    ),
) -> Response:
    del auth
    view = build_dashboard(db)
    preferences = _preferences(
        theme,
        palette,
        None,
    )

    svg = category_chart_svg(
        view.categories,
        preferences,
    )

    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "no-store"
        },
    )


@router.get(
    "/charts/comparison.svg",
    include_in_schema=False,
)
def comparison_chart(
    auth: AuthContext = Depends(
        require_auth_context
    ),
    db: Session = Depends(
        get_db_session
    ),
    theme: str | None = Cookie(
        default=None,
        alias=THEME_COOKIE,
    ),
    palette: str | None = Cookie(
        default=None,
        alias=PALETTE_COOKIE,
    ),
) -> Response:
    del auth
    current, previous = (
        _latest_month_totals(db)
    )
    preferences = _preferences(
        theme,
        palette,
        None,
    )

    svg = comparison_chart_svg(
        current,
        previous,
        preferences,
    )

    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "no-store"
        },
    )


@router.get(
    "/admin",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def admin_page(
    request: Request,
    auth: AuthContext = Depends(
        require_auth_context
    ),
    db: Session = Depends(
        get_db_session
    ),
    theme: str | None = Cookie(
        default=None,
        alias=THEME_COOKIE,
    ),
    csrf_cookie: str | None = Cookie(
        default=None,
        alias=CSRF_COOKIE_NAME,
    ),
) -> HTMLResponse:
    if auth.user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail=(
                "Administrator access required."
            ),
        )

    users = db.scalars(
        select(User).order_by(
            User.username
        )
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "auth": auth,
            "users": users,
            "preferences": (
                _preferences(
                    theme,
                    None,
                    None,
                )
            ),
            "csrf_token": (
                csrf_cookie or ""
            ),
            "single_household": True,
        },
        headers={
            "Cache-Control": "no-store"
        },
    )


@router.get(
    "/admin/preview/{user_id}",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def admin_preview_user(
    user_id: int,
    request: Request,
    auth: AuthContext = Depends(
        require_auth_context
    ),
    db: Session = Depends(
        get_db_session
    ),
    theme: str | None = Cookie(
        default=None,
        alias=THEME_COOKIE,
    ),
    palette: str | None = Cookie(
        default=None,
        alias=PALETTE_COOKIE,
    ),
    layout: str | None = Cookie(
        default=None,
        alias=LAYOUT_COOKIE,
    ),
) -> HTMLResponse:
    """
    Safe first-step support preview.

    This does not mutate the administrator's authenticated identity and is
    intentionally not called full impersonation yet. Real impersonation needs
    an auditable server-side support-session model and household authorization.
    """
    if auth.user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail=(
                "Administrator access required."
            ),
        )

    target = db.get(
        User,
        user_id,
    )

    if target is None:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    view = build_dashboard(db)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "auth": auth,
            "view": view,
            "preferences": _preferences(
                theme,
                palette,
                layout,
            ),
            "csrf_token": "",
            "single_household": True,
            "support_preview_user": (
                target
            ),
        },
        headers={
            "Cache-Control": "no-store"
        },
    )
