from __future__ import annotations

import copy

import pytest

from taskrunnerx.worker.worker import HANDLERS


@pytest.mark.anyio("asyncio")
async def test_task_handlers_preserve_payload_inputs() -> None:
    sample_payloads = [
        {"text": "hello"},
        {"source": "scheduler"},
        {"value": 42},
    ]

    for handler in HANDLERS.values():
        for payload in sample_payloads:
            snapshot = copy.deepcopy(payload)
            await handler(copy.deepcopy(payload))
            assert payload == snapshot
