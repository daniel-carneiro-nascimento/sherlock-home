import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.shutdown import wait_for_shutdown


@asynccontextmanager
async def lifespan(app: FastAPI):
    shutdown_task = asyncio.create_task(wait_for_shutdown())

    try:
        yield
    finally:
        shutdown_task.cancel()

        try:
            await shutdown_task
        except asyncio.CancelledError:
            pass
