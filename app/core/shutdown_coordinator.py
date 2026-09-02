import asyncio
import os
import signal

from app.core.shutdown import wait_for_shutdown


async def shutdown_coordinator() -> None:
    """
    Wait for a controlled shutdown request and then ask the
    application process to terminate gracefully.

    SIGTERM is handled by Uvicorn as a graceful shutdown request.
    """
    await wait_for_shutdown()

    await asyncio.sleep(0)

    os.kill(
        os.getpid(),
        signal.SIGTERM,
    )
