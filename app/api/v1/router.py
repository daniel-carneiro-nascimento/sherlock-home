from fastapi import APIRouter

from app.api.v1.auth_routes import (
    router as auth_router,
)
from app.api.v1.config_routes import (
    router as config_router,
)


router = APIRouter(
    prefix="/api/v1",
)

router.include_router(
    auth_router
)

router.include_router(
    config_router
)
