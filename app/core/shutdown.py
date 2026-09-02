import asyncio


_shutdown_event = asyncio.Event()


def request_shutdown() -> None:
    """
    Request a graceful application shutdown.

    This does not immediately kill the process.
    It signals the application lifecycle to terminate safely.
    """
    _shutdown_event.set()


def shutdown_requested() -> bool:
    return _shutdown_event.is_set()


async def wait_for_shutdown() -> None:
    await _shutdown_event.wait()


def reset_shutdown_state() -> None:
    """
    Intended primarily for tests.
    """
    _shutdown_event.clear()
