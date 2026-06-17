"""
app/core/batch_store.py
-------------------------
The durable batch store. One batch = one ingestion request (from KNIME or upstream).

Raw JSON is stored exactly as received and is NEVER mutated by anything downstream.
That's the contract the "raw JSON inspection" endpoint (/api/batch/{id}) depends on.

Threads: uses connection-per-query (thread-safe), not a long-lived connection pool.
"""

import json
import logging
import uuid
from datetime import datetime, timezone

from app.db import get_connection

logger = logging.getLogger(__name__)


def _now() -> str:
    """Current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


class BatchStore:
    """Thin wrapper around SQLite batches table."""

    def create(
        self,
        entity: str,
        raw: dict | list,
        normalized: list[dict],
        flattened: list[dict],
    ) -> dict:
        """
        Create a new batch. Store raw JSON exactly as received (no mutation).
        Returns the full batch dict.
        """
        batch_id = str(uuid.uuid4())
        now = _now()
        conn = get_connection()
        try:
            conn.execute(
                """
                INSERT INTO batches (id, entity, raw, normalized, flattened,
                                      status, count, results, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'pending', ?, NULL, ?, ?)
                """,
                (
                    batch_id,
                    entity,
                    json.dumps(raw),
                    json.dumps(normalized),
                    json.dumps(flattened),
                    len(flattened),
                    now,
                    now,
                ),
            )
            conn.commit()
            logger.debug(f"Created batch {batch_id} for entity {entity}")
        finally:
            conn.close()

        return self.get(batch_id)

    def get(self, batch_id: str) -> dict | None:
        """Retrieve a single batch by id. Returns None if not found."""
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM batches WHERE id = ?",
                (batch_id,),
            ).fetchone()
        finally:
            conn.close()

        return self._row_to_dict(row) if row else None

    def list(self, entity: str | None = None) -> list[dict]:
        """
        List batches, newest first.
        If entity is specified, filter by that entity.
        """
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

        return [self._row_to_dict(r) for r in rows]

    def update_status(self, batch_id: str, status: str) -> None:
        """Update batch status (e.g., 'pending' -> 'validating')."""
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE batches SET status = ?, updated_at = ? WHERE id = ?",
                (status, _now(), batch_id),
            )
            conn.commit()
            logger.debug(f"Updated batch {batch_id} status to {status}")
        finally:
            conn.close()

    def update_results(
        self,
        batch_id: str,
        results: dict,
        status: str | None = None,
    ) -> None:
        """
        Update batch results (per-row outcomes from validate/load).
        Optionally update status at the same time.
        """
        conn = get_connection()
        try:
            if status:
                conn.execute(
                    "UPDATE batches SET results = ?, status = ?, updated_at = ? WHERE id = ?",
                    (json.dumps(results), status, _now(), batch_id),
                )
            else:
                conn.execute(
                    "UPDATE batches SET results = ?, updated_at = ? WHERE id = ?",
                    (json.dumps(results), _now(), batch_id),
                )
            conn.commit()
            logger.debug(f"Updated batch {batch_id} results")
        finally:
            conn.close()

    @staticmethod
    def _row_to_dict(row) -> dict:
        """Convert a sqlite3.Row to a plain dict, deserializing JSON fields."""
        return {
            "id": row["id"],
            "entity": row["entity"],
            "raw": json.loads(row["raw"]),
            "normalized": json.loads(row["normalized"]),
            "flattened": json.loads(row["flattened"]),
            "status": row["status"],
            "count": row["count"],
            "results": json.loads(row["results"]) if row["results"] else None,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


# Global singleton instance
batch_store = BatchStore()