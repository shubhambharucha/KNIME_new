"""
app/api/batches.py
---------------------
POST /api/upload-json   — KNIME posts ANY valid JSON; becomes a batch, status=pending
GET  /api/batch/{id}    — raw JSON inspection endpoint (exact as received)
GET  /api/batches       — list batches, optionally filtered by entity
GET  /api/debug/last    — return most recently uploaded batch

DESIGN: Accepts ANY valid JSON (no Pydantic schema enforcement).
  - If JSON has top-level "entity" field → use it
  - Else if entity name detected in data structure → use it
  - Else → default to "unknown"

Stores raw JSON exactly as received (never mutated).
Logs all incoming payloads for audit trail.
"""

import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.core.batch_store import batch_store
from app.core.normalize import flatten, normalize
from app.core.registry import ENTITY_MAP

logger = logging.getLogger(__name__)

router = APIRouter()


def _detect_entity(raw_json: dict) -> str:
    """
    HARDCODED for testing: always return "Customer".
    In production, can extend to detect entity from JSON structure.
    """
    return "Customer"


def _apply_entity_config(records: list[dict], config_module) -> list[dict]:
    """Apply COLUMN_ALIASES + DEFAULTS to every flattened record."""
    aliases = getattr(config_module, "COLUMN_ALIASES", {})
    defaults = getattr(config_module, "DEFAULTS", {})

    out = []
    for record in records:
        renamed = {aliases.get(k, k): v for k, v in record.items()}
        for col, value in defaults.items():
            renamed.setdefault(col, value)
        out.append(renamed)
    return out


@router.post("/api/upload-json")
async def upload_json(request: Request):
    """
    Accept ANY valid JSON. Parse it, normalize it, flatten it, store raw + transformed.
    
    Returns: { "ok": bool, "batch_id": str, "entity": str, "count": int, "status": str }
    """
    try:
        raw_json = await request.json()
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON received: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Detect entity (explicit, inferred, or default)
    entity = _detect_entity(raw_json)

    # Structural transforms: normalize to list[dict], flatten nesting
    normalized = normalize(raw_json)
    flattened = [flatten(r) for r in normalized]

    # Apply semantic field mapping if entity is registered
    entry = ENTITY_MAP.get(entity)
    if entry is not None:
        flattened = _apply_entity_config(flattened, entry["config"])

    # Create batch in store
    batch = batch_store.create(
        entity=entity,
        raw=raw_json,  # Store raw exactly as received
        normalized=normalized,
        flattened=flattened
    )

    # Log the ingestion
    logger.info(
        f"Received batch {batch['id']}: entity={entity}, count={len(flattened)}, "
        f"payload_size={len(json.dumps(raw_json))} bytes"
    )

    return {
        "ok": True,
        "batch_id": batch["id"],
        "entity": batch["entity"],
        "count": batch["count"],
        "status": batch["status"],
    }


@router.get("/api/batch/{batch_id}")
async def get_batch(batch_id: str):
    """
    Return a single batch, including the raw JSON payload exactly as received.
    This endpoint is critical for debugging upstream systems (e.g., KNIME).
    """
    batch = batch_store.get(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail=f"Batch not found: {batch_id}")
    return batch


@router.get("/api/batches")
async def list_batches(entity: str | None = None):
    """
    List all batches, optionally filtered by entity.
    Returns: { "batches": [...] }
    """
    batches = batch_store.list(entity=entity)
    return {"batches": batches}


@router.get("/api/debug/last")
async def debug_last():
    """
    Return the most recently uploaded batch (for quick debugging).
    Useful for checking what just came in from KNIME.
    """
    batches = batch_store.list()
    if not batches:
        raise HTTPException(status_code=404, detail="No batches yet")
    return batches[0]  # list() returns DESC by created_at