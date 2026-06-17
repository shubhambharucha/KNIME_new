"""
app/core/batch_store.py
------------------------
Simple CRUD wrapper for batches table in SQLite.
Batches are immutable once created; status and results are updated in-place.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any

from app.db import get_connection, _lock

logger = logging.getLogger(__name__)


class BatchStore:
    """In-memory + SQLite batch storage."""

    def create(
        self,
        entity: str,
        raw: dict,
        normalized: list[dict],
        flattened: list[dict],
    ) -> dict:
        """Create a new batch. Returns batch dict."""
        batch_id = str(uuid.uuid4())[:12]
        now = datetime.utcnow().isoformat() + "Z"

        batch = {
            "id": batch_id,
            "entity": entity,
            "raw": raw,
            "normalized": normalized,
            "flattened": flattened,
            "status": "pending",
            "count": len(flattened),
            "results": None,
            "created_at": now,
            "updated_at": now,
        }

        with _lock:
            conn = get_connection()
            try:
                conn.execute(
                    """
                    INSERT INTO batches
                    (id, entity, raw, normalized, flattened, status, count, results, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        batch_id,
                        entity,
                        json.dumps(raw),
                        json.dumps(normalized),
                        json.dumps(flattened),
                        "pending",
                        len(flattened),
                        None,
                        now,
                        now,
                    ),
                )
                conn.commit()
            finally:
                conn.close()

        logger.info(f"Created batch {batch_id}: {entity}, {len(flattened)} rows")
        return batch

    def get(self, batch_id: str) -> dict | None:
        """Fetch a single batch by ID."""
        with _lock:
            conn = get_connection()
            try:
                row = conn.execute(
                    "SELECT * FROM batches WHERE id = ?", (batch_id,)
                ).fetchone()
            finally:
                conn.close()

        if not row:
            return None

        return self._row_to_dict(row)

    def list(self, entity: str | None = None) -> list[dict]:
        """List all batches (optionally filtered by entity), newest first."""
        with _lock:
            conn = get_connection()
            try:
                if entity:
                    rows = conn.execute(
                        "SELECT * FROM batches WHERE entity = ? ORDER BY created_at DESC",
                        (entity,),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT * FROM batches ORDER BY created_at DESC"
                    ).fetchall()
            finally:
                conn.close()

        return [self._row_to_dict(row) for row in rows]

    def update_status(self, batch_id: str, status: str, results: Any = None) -> bool:
        """Update batch status and optionally results. Returns success."""
        now = datetime.utcnow().isoformat() + "Z"
        results_json = json.dumps(results) if results is not None else None

        with _lock:
            conn = get_connection()
            try:
                cursor = conn.execute(
                    """
                    UPDATE batches
                    SET status = ?, results = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (status, results_json, now, batch_id),
                )
                conn.commit()
                success = cursor.rowcount > 0
            finally:
                conn.close()

        if success:
            logger.info(f"Updated batch {batch_id}: status={status}")
        return success

    @staticmethod
    def _row_to_dict(row: Any) -> dict:
        """Convert sqlite3.Row to dict, parsing JSON fields."""
        batch = dict(row)
        if batch.get("raw"):
            batch["raw"] = json.loads(batch["raw"])
        if batch.get("normalized"):
            batch["normalized"] = json.loads(batch["normalized"])
        if batch.get("flattened"):
            batch["flattened"] = json.loads(batch["flattened"])
        if batch.get("results"):
            batch["results"] = json.loads(batch["results"])
        return batch


# Singleton instance
batch_store = BatchStore()