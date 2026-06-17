"""
app/api/operations.py
---------------------
POST /api/load     — Load batch(es) into QAD
GET  /api/status   — Check overall pipeline status
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.core.batch_store import batch_store
from app.core.registry import get_entity, list_entities
from app.entities.customer.loader import TokenManager

logger = logging.getLogger(__name__)

router = APIRouter()

# Global token manager (one per API instance; refreshes on 401)
_token_manager = TokenManager()


@router.post("/api/load")
async def load_batch(batch_id: str):
    """
    Load a single batch into QAD.
    
    Flow:
      1. Fetch batch from store
      2. Look up entity loader
      3. Call loader.load_batch(flattened_records, token_manager)
      4. Store results, update status → loading | loaded | loaded_with_errors
    
    Returns: { "ok": bool, "batch_id": str, "status": str, "results": [...] }
    """
    # Fetch batch
    batch = batch_store.get(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail=f"Batch not found: {batch_id}")

    entity = batch["entity"]
    flattened = batch["flattened"]

    # Look up entity loader
    entity_entry = get_entity(entity)
    if entity_entry is None:
        raise HTTPException(status_code=400, detail=f"Unknown entity: {entity}")

    loader = entity_entry["loader"]

    # Update status to "loading"
    batch_store.update_status(batch_id, "loading")

    # Load batch
    try:
        results = loader.load_batch(flattened, _token_manager)
    except Exception as e:
        logger.error(f"Loader error for batch {batch_id}: {e}")
        batch_store.update_status(batch_id, "loaded_with_errors", [])
        raise HTTPException(status_code=500, detail=f"Loader error: {str(e)}")

    # Determine final status
    ok_count = sum(1 for r in results if r.get("ok"))
    fail_count = len(results) - ok_count

    if fail_count == 0:
        final_status = "loaded"
    else:
        final_status = "loaded_with_errors"

    # Store results and update status
    batch_store.update_status(batch_id, final_status, results)

    logger.info(
        f"Batch {batch_id} ({entity}): {ok_count} OK, {fail_count} FAILED"
    )

    return {
        "ok": fail_count == 0,
        "batch_id": batch_id,
        "entity": entity,
        "status": final_status,
        "summary": {
            "total": len(results),
            "ok": ok_count,
            "failed": fail_count,
        },
        "results": results,
    }


@router.post("/api/load-all")
async def load_all(entity: str | None = None):
    """
    Load all pending batches (optionally filtered by entity).
    
    Returns: { "batches_loaded": int, "results": [...] }
    """
    batches = batch_store.list(entity=entity)
    pending = [b for b in batches if b["status"] == "pending"]

    if not pending:
        return {"batches_loaded": 0, "results": []}

    results = []
    for batch in pending:
        try:
            load_result = await load_batch(batch["id"])
            results.append(load_result)
        except HTTPException as e:
            results.append({
                "batch_id": batch["id"],
                "ok": False,
                "error": e.detail,
            })

    return {
        "batches_loaded": len([r for r in results if r.get("ok")]),
        "results": results,
    }


@router.get("/api/status")
async def status():
    """
    Return overall pipeline status: count of batches by status.
    """
    batches = batch_store.list()
    entities = list_entities()

    status_counts = {}
    for batch in batches:
        s = batch["status"]
        status_counts[s] = status_counts.get(s, 0) + 1

    return {
        "entities": entities,
        "total_batches": len(batches),
        "by_status": status_counts,
    }