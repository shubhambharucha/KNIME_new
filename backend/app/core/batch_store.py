"""
app/core/batch_store.py
-------------------------
The thing the requirements doc calls BATCH_STORE, made durable.

One API request = one batch. Raw JSON is stored exactly as received and is
never mutated by anything downstream — that's the contract the "raw JSON
inspection" endpoint depends on.
"""

import json
import uuid
from datetime import datetime, timezone

from app.db import get_connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class BatchStore:

    def create(self, entity: str, raw, normalized: list[dict], flattened: list[dict]) -> dict:
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
                    batch_id, entity,
                    json.dumps(raw), json.dumps(normalized), json.dumps(flattened),
                    len(flattened), now, now,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return self.get(batch_id)

    def get(self, batch_id: str) -> dict | None:
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM batches WHERE id = ?", (batch_id,)).fetchone()
        finally:
            conn.close()
        return self._row_to_dict(row) if row else None

    def list(self, entity: str | None = None) -> list[dict]:
        conn = get_connection()
        try:
            if entity:
                rows = conn.execute(
                    "SELECT * FROM batches WHERE entity = ? ORDER BY created_at DESC", (entity,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM batches ORDER BY created_at DESC").fetchall()
        finally:
            conn.close()
        return [self._row_to_dict(r) for r in rows]

    def update_status(self, batch_id: str, status: str) -> None:
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE batches SET status = ?, updated_at = ? WHERE id = ?",
                (status, _now(), batch_id),
            )
            conn.commit()
        finally:
            conn.close()

    def update_results(self, batch_id: str, results: dict, status: str | None = None) -> None:
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
        finally:
            conn.close()

    @staticmethod
    def _row_to_dict(row) -> dict:
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


batch_store = BatchStore()
