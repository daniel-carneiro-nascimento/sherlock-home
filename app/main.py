from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.lifecycle import lifespan
from app.core.security_enforcer import SecurityPolicyError


app = FastAPI(
    title="Sherlock Home",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(SecurityPolicyError)
async def security_policy_exception_handler(
    request: Request,
    exc: SecurityPolicyError,
):
    return JSONResponse(
        status_code=403,
        content={
            "error": "security_policy_violation",
            "message": str(exc),
        },
    )


app.include_router(router)
