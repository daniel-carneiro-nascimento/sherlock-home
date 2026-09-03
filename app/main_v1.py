"""
Phase 4 API v1 entrypoint.

This preserves the existing app.main application and attaches the
authenticated /api/v1 router without replacing the legacy FastAPI
application or its lifecycle/security handlers.

Run with:

    python -m scripts.run_https
"""

from app.main import app
from app.api.v1.router import router as api_v1_router


def _api_v1_is_registered() -> bool:
    """
    Check existing FastAPI/Starlette routes defensively.

    Some current FastAPI/Starlette versions may place internal router
    objects in app.routes that do not expose a ``path`` attribute.
    """
    for route in app.routes:
        path = getattr(route, "path", None)

        if (
            isinstance(path, str)
            and path.startswith("/api/v1")
        ):
            return True

    return False


if not _api_v1_is_registered():
    app.include_router(api_v1_router)
