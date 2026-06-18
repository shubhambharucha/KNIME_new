"""
app/api/batches.py
---------------------
POST /api/upload-json   — Receive JSON, store batch, auto-load to QAD
GET  /api/batch/{id}    — Inspect batch
GET  /api/batches       — List batches
GET  /api/debug/last    — Most recent batch
"""

import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Body

import app.core.batch_store
from app.core.registry import ENTITY_MAP

from app.core.normalize import flatten, normalize

from app.entities.customer.loader import (
    TokenManager,
    load_batch,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# One token manager per API instance
_token_manager = TokenManager()


def _detect_entity(raw_json: dict) -> str:
    """
    Currently hardcoded.
    Can be expanded later.
    """
    return "Customer"


def _apply_entity_config(records: list[dict], config_module) -> list[dict]:
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
async def upload_json(raw_json: Any = Body(...)):
    """
    Receive JSON
        ↓
    Normalize
        ↓
    Flatten
        ↓
    Store Batch
        ↓
    Auto Load
        ↓
    Return Results
    """

    # ---------------------------------------------------------
    # Detect entity
    # ---------------------------------------------------------

    entity = _detect_entity(raw_json)

    # ---------------------------------------------------------
    # Normalize + Flatten
    # ---------------------------------------------------------

    normalized = normalize(raw_json)
    flattened = [flatten(r) for r in normalized]

    # ---------------------------------------------------------
    # Entity config (if any)
    # ---------------------------------------------------------

    entry = ENTITY_MAP.get(entity)

    if entry is not None:
        flattened = _apply_entity_config(
            flattened,
            entry["config"]
        )

    # ---------------------------------------------------------
    # Store batch
    # ---------------------------------------------------------

    batch = app.core.batch_store.batch_store.create(
        entity=entity,
        raw=raw_json,
        normalized=normalized,
        flattened=flattened,
    )

    logger.info(
        f"Received batch {batch['id']} | "
        f"entity={entity} | "
        f"records={len(flattened)}"
    )

    # ---------------------------------------------------------
    # AUTO LOAD
    # ---------------------------------------------------------

    try:

        results = load_batch(
            flattened,
            _token_manager,
        )

        ok_count = sum(
            1 for r in results
            if r.get("ok")
        )

        fail_count = len(results) - ok_count

        status = (
            "loaded"
            if fail_count == 0
            else "loaded_with_errors"
        )

        app.core.batch_store.batch_store.update_status(
            batch["id"],
            status,
            results,
        )

        logger.info(
            f"Batch {batch['id']} completed | "
            f"OK={ok_count} FAILED={fail_count}"
        )

        return {
            "ok": fail_count == 0,
            "batch_id": batch["id"],
            "entity": entity,
            "status": status,
            "summary": {
                "total": len(results),
                "ok": ok_count,
                "failed": fail_count,
            },
            "results": results,
        }

    except Exception as exc:

        logger.exception(
            f"Auto-load failed for batch {batch['id']}"
        )

        app.core.batch_store.batch_store.update_status(
            batch["id"],
            "loaded_with_errors",
            [{
                "ok": False,
                "error": str(exc)
            }],
        )

        raise HTTPException(
            status_code=500,
            detail=f"Auto-load failed: {str(exc)}"
        )


@router.get("/api/batch/{batch_id}")
async def get_batch(batch_id: str):

    batch = app.core.batch_store.batch_store.get(batch_id)

    if batch is None:
        raise HTTPException(
            status_code=404,
            detail=f"Batch not found: {batch_id}"
        )

    return batch


@router.get("/api/batches")
async def list_batches(entity: str | None = None):

    batches = app.core.batch_store.batch_store.list(
        entity=entity
    )

    return {
        "batches": batches
    }


@router.get("/api/debug/last")
async def debug_last():

    batches = app.core.batch_store.batch_store.list()

    if not batches:
        raise HTTPException(
            status_code=404,
            detail="No batches yet"
        )

    return batches[0]