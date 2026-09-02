import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.shutdown_coordinator import shutdown_coordinator


@asynccontextmanager
async def lifespan(app: FastAPI):
    coordinator_task = asyncio.create_task(
        shutdown_coordinator()
    )

    try:
        yield

    finally:
        coordinator_task.cancel()

        try:
            await coordinator_task
        except asyncio.CancelledError:
            pass
