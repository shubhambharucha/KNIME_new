"""
app/api/operations.py
------------------------
POST /api/validate  { "batch_ids": [...] }
POST /api/load       { "batch_ids": [...] }

Same SSE event encoding as before (so frontend parsing loop barely changes),
but the unit of work is now a row inside a batch, not a row inside an xlsx.

Event types: batch_start, progress, row_result, batch_result, done, error
"""

import asyncio
import logging
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.batch_store import batch_store
from app.core.events import sse
from app.core.registry import ENTITY_MAP, is_implemented
from app.qad.auth import TokenManager

logger = logging.getLogger(__name__)

router = APIRouter()

SSE_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}


class BatchOperationRequest(BaseModel):
    batch_ids: list[str]


async def validate_stream(batch_ids: list[str]) -> AsyncGenerator[str, None]:
    """
    Validate a list of batches. For each batch:
      - Load the batch from store
      - Look up its entity in ENTITY_MAP
      - Run validate_row() on each flattened record
      - Stream per-row results via SSE
      - Update batch status + results in store
    """
    loop = asyncio.get_event_loop()

    for batch_id in batch_ids:
        batch = batch_store.get(batch_id)
        if batch is None:
            msg = f"Batch not found: {batch_id}"
            logger.error(msg)
            yield sse({"type": "error", "message": msg})
            continue

        entity = batch["entity"]
        if not is_implemented(entity):
            msg = f"Entity '{entity}' is not yet ported to the new architecture"
            logger.warning(msg)
            yield sse({"type": "error", "message": msg})
            continue

        entry = ENTITY_MAP[entity]
        validate_row = entry["validate_row"]
        records = batch["flattened"]
        total = len(records)

        batch_store.update_status(batch_id, "validating")
        logger.info(f"Starting validation for batch {batch_id} ({entity}): {total} rows")
        
        yield sse({
            "type": "batch_start",
            "batch_id": batch_id,
            "entity": entity,
            "count": total,
        })
        await asyncio.sleep(0)

        passed = 0
        failed = 0
        row_results = []

        for i, record in enumerate(records, start=1):
            try:
                errors = await loop.run_in_executor(None, validate_row, record)
                ok = len(errors) == 0
            except Exception as e:
                logger.exception(f"Validation error in batch {batch_id} row {i}: {e}")
                ok = False
                errors = [str(e)]

            if ok:
                passed += 1
            else:
                failed += 1

            row_results.append({"row": i, "ok": ok, "errors": errors})

            yield sse({
                "type": "row_result",
                "batch_id": batch_id,
                "row": i,
                "total": total,
                "ok": ok,
                "errors": errors,
            })
            await asyncio.sleep(0)

        status = "validated" if failed == 0 else "validated_with_errors"
        batch_store.update_results(
            batch_id,
            {"passed": passed, "failed": failed, "rows": row_results},
            status=status,
        )
        logger.info(f"Validation complete for batch {batch_id}: {passed} passed, {failed} failed")

        yield sse({
            "type": "batch_result",
            "batch_id": batch_id,
            "entity": entity,
            "passed": passed,
            "failed": failed,
        })
        await asyncio.sleep(0)

    yield sse({"type": "done", "message": "Validation complete"})


async def load_stream(batch_ids: list[str]) -> AsyncGenerator[str, None]:
    """
    Load a list of batches into QAD. For each batch:
      - Load the batch from store
      - Look up its entity in ENTITY_MAP
      - Run load_row() on each flattened record (with shared TokenManager)
      - Stream per-row results via SSE
      - Update batch status + results in store
    """
    loop = asyncio.get_event_loop()
    tm = TokenManager()  # shared token across all batches in this load run

    for batch_id in batch_ids:
        batch = batch_store.get(batch_id)
        if batch is None:
            msg = f"Batch not found: {batch_id}"
            logger.error(msg)
            yield sse({"type": "error", "message": msg})
            continue

        entity = batch["entity"]
        if not is_implemented(entity):
            msg = f"Entity '{entity}' is not yet ported to the new architecture"
            logger.warning(msg)
            yield sse({"type": "error", "message": msg})
            continue

        entry = ENTITY_MAP[entity]
        load_row = entry["load_row"]
        records = batch["flattened"]
        total = len(records)

        batch_store.update_status(batch_id, "loading")
        logger.info(f"Starting load for batch {batch_id} ({entity}): {total} rows")
        
        yield sse({
            "type": "batch_start",
            "batch_id": batch_id,
            "entity": entity,
            "count": total,
        })
        await asyncio.sleep(0)

        passed = 0
        failed = 0
        row_results = []

        for i, record in enumerate(records, start=1):
            try:
                ok, error_msg = await loop.run_in_executor(None, load_row, record, tm)
            except Exception as e:
                logger.exception(f"Load error in batch {batch_id} row {i}: {e}")
                ok = False
                error_msg = str(e)

            if ok:
                passed += 1
            else:
                failed += 1

            row_results.append({"row": i, "ok": ok, "error": error_msg})

            yield sse({
                "type": "row_result",
                "batch_id": batch_id,
                "row": i,
                "total": total,
                "ok": ok,
                "error": error_msg,
            })
            await asyncio.sleep(0)

        status = "loaded" if failed == 0 else "loaded_with_errors"
        batch_store.update_results(
            batch_id,
            {"passed": passed, "failed": failed, "rows": row_results},
            status=status,
        )
        logger.info(f"Load complete for batch {batch_id}: {passed} passed, {failed} failed")

        yield sse({
            "type": "batch_result",
            "batch_id": batch_id,
            "entity": entity,
            "passed": passed,
            "failed": failed,
        })
        await asyncio.sleep(0)

    yield sse({"type": "done", "message": "Load complete"})


@router.post("/api/validate")
async def api_validate(req: BatchOperationRequest):
    """Stream validation progress for one or more batches."""
    return StreamingResponse(
        validate_stream(req.batch_ids),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.post("/api/load")
async def api_load(req: BatchOperationRequest):
    """Stream load progress for one or more batches."""
    return StreamingResponse(
        load_stream(req.batch_ids),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )