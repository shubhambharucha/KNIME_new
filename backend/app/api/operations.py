"""
app/api/operations.py
------------------------
POST /api/validate  { "batch_ids": [...] }
POST /api/load       { "batch_ids": [...] }

Same SSE event encoding as the old main.py (so the existing frontend's parsing
loop barely needs to change), but the unit of work is now a row inside a batch,
not a row inside an xlsx file inside a folder.

Event types: batch_start, progress, row_result, batch_result, done, error
"""

import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.batch_store import batch_store
from app.core.events import sse
from app.core.registry import ENTITY_MAP
from app.qad.auth import TokenManager

router = APIRouter()

SSE_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}


class BatchOperationRequest(BaseModel):
    batch_ids: list[str]


async def validate_stream(batch_ids: list[str]) -> AsyncGenerator[str, None]:
    loop = asyncio.get_event_loop()

    for batch_id in batch_ids:
        batch = batch_store.get(batch_id)
        if batch is None:
            yield sse({"type": "error", "message": f"Batch not found: {batch_id}"})
            continue

        entry = ENTITY_MAP.get(batch["entity"])
        if entry is None:
            yield sse({"type": "error", "message": f"Entity '{batch['entity']}' is not yet ported to the new architecture"})
            continue

        validate_row = entry["validate_row"]
        records = batch["flattened"]
        total = len(records)

        batch_store.update_status(batch_id, "validating")
        yield sse({"type": "batch_start", "batch_id": batch_id, "entity": batch["entity"], "count": total})
        await asyncio.sleep(0)

        passed = 0
        failed = 0
        row_results = []

        for i, record in enumerate(records, start=1):
            errors = await loop.run_in_executor(None, validate_row, record)
            ok = len(errors) == 0
            if ok:
                passed += 1
            else:
                failed += 1
            row_results.append({"row": i, "ok": ok, "errors": errors})

            yield sse({
                "type": "row_result", "batch_id": batch_id, "row": i, "total": total,
                "ok": ok, "errors": errors,
            })
            await asyncio.sleep(0)

        status = "validated" if failed == 0 else "validated_with_errors"
        batch_store.update_results(batch_id, {"passed": passed, "failed": failed, "rows": row_results}, status=status)

        yield sse({"type": "batch_result", "batch_id": batch_id, "entity": batch["entity"], "passed": passed, "failed": failed})
        await asyncio.sleep(0)

    yield sse({"type": "done", "message": "Validation complete"})


async def load_stream(batch_ids: list[str]) -> AsyncGenerator[str, None]:
    loop = asyncio.get_event_loop()
    tm = TokenManager()  # one token shared across this whole load run

    for batch_id in batch_ids:
        batch = batch_store.get(batch_id)
        if batch is None:
            yield sse({"type": "error", "message": f"Batch not found: {batch_id}"})
            continue

        entry = ENTITY_MAP.get(batch["entity"])
        if entry is None:
            yield sse({"type": "error", "message": f"Entity '{batch['entity']}' is not yet ported to the new architecture"})
            continue

        load_row = entry["load_row"]
        records = batch["flattened"]
        total = len(records)

        batch_store.update_status(batch_id, "loading")
        yield sse({"type": "batch_start", "batch_id": batch_id, "entity": batch["entity"], "count": total})
        await asyncio.sleep(0)

        passed = 0
        failed = 0
        row_results = []

        for i, record in enumerate(records, start=1):
            ok, error_msg = await loop.run_in_executor(None, load_row, record, tm)
            if ok:
                passed += 1
            else:
                failed += 1
            row_results.append({"row": i, "ok": ok, "error": error_msg})

            yield sse({
                "type": "row_result", "batch_id": batch_id, "row": i, "total": total,
                "ok": ok, "error": error_msg,
            })
            await asyncio.sleep(0)

        status = "loaded" if failed == 0 else "loaded_with_errors"
        batch_store.update_results(batch_id, {"passed": passed, "failed": failed, "rows": row_results}, status=status)

        yield sse({"type": "batch_result", "batch_id": batch_id, "entity": batch["entity"], "passed": passed, "failed": failed})
        await asyncio.sleep(0)

    yield sse({"type": "done", "message": "Load complete"})


@router.post("/api/validate")
async def api_validate(req: BatchOperationRequest):
    return StreamingResponse(validate_stream(req.batch_ids), media_type="text/event-stream", headers=SSE_HEADERS)


@router.post("/api/load")
async def api_load(req: BatchOperationRequest):
    return StreamingResponse(load_stream(req.batch_ids), media_type="text/event-stream", headers=SSE_HEADERS)
