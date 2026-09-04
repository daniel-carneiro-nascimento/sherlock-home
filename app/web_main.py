"""
Sherlock Home server-rendered web entrypoint.

This preserves the existing API/lifecycle and mounts the first F1 web shell.
Run locally with:

    python -m scripts.run_web_https
"""

from fastapi.staticfiles import (
    StaticFiles,
)

from app.main_v1 import app
from app.web.router import (
    WEB_ROOT,
    router as web_router,
)


def _web_is_registered() -> bool:
    for route in app.routes:
        path = getattr(
            route,
            "path",
            None,
        )
        if (
            isinstance(path, str)
            and path.startswith("/web")
        ):
            return True
    return False


if not _web_is_registered():
    app.include_router(web_router)


_static_registered = any(
    getattr(route, "name", None)
    == "web-static"
    for route in app.routes
)

if not _static_registered:
    app.mount(
        "/web/static",
        StaticFiles(
            directory=str(
                WEB_ROOT / "static"
            )
        ),
        name="web-static",
    )
