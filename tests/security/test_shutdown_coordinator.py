import asyncio
import os
import signal

import pytest

from app.core.shutdown import (
    request_shutdown,
    reset_shutdown_state,
)
from app.core.shutdown_coordinator import shutdown_coordinator


@pytest.fixture(autouse=True)
def reset_shutdown():
    reset_shutdown_state()
    yield
    reset_shutdown_state()


@pytest.mark.asyncio
async def test_shutdown_coordinator_sends_sigterm(monkeypatch):
    calls = []

    def fake_kill(pid, sig):
        calls.append((pid, sig))

    monkeypatch.setattr(os, "kill", fake_kill)

    task = asyncio.create_task(
        shutdown_coordinator()
    )

    request_shutdown()

    await asyncio.wait_for(
        task,
        timeout=1,
    )

    assert len(calls) == 1

    pid, sig = calls[0]

    assert pid == os.getpid()
    assert sig == signal.SIGTERM
