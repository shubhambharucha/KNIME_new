"""
app/api/batches.py
---------------------
POST /api/upload-json   — KNIME posts JSON here; becomes a batch, status=pending
GET  /api/batch/{id}    — raw JSON inspection endpoint required by the spec (#12)
GET  /api/batches       — list batches, optionally filtered by entity
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.batch_store import batch_store
from app.core.normalize import flatten, normalize
from app.core.registry import ENTITY_MAP

router = APIRouter()


class UploadJsonRequest(BaseModel):
    entity: str
    data: Any  # intentionally untyped — "accept all input", never 422 on shape


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
async def upload_json(req: UploadJsonRequest):
    # Per design rule #3: never reject on schema mismatch, even for an
    # unrecognized entity name — store it so it's visible/inspectable,
    # just don't try to validate/load it later.
    raw = {"entity": req.entity, "data": req.data}

    normalized = normalize(req.data)
    flattened = [flatten(r) for r in normalized]

    entry = ENTITY_MAP.get(req.entity)
    if entry is not None:
        flattened = _apply_entity_config(flattened, entry["config"])

    batch = batch_store.create(entity=req.entity, raw=raw, normalized=normalized, flattened=flattened)

    return {
        "ok": True,
        "batch_id": batch["id"],
        "entity": batch["entity"],
        "count": batch["count"],
        "status": batch["status"],
    }


@router.get("/api/batch/{batch_id}")
async def get_batch(batch_id: str):
    batch = batch_store.get(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail=f"Batch not found: {batch_id}")
    return batch


@router.get("/api/batches")
async def list_batches(entity: str | None = None):
    return {"batches": batch_store.list(entity=entity)}
