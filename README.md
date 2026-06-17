# KNIME Data Loader — new structure

## What's real vs. what's a stub

- **`backend/app/`** — runnable FastAPI app. `Customer` is fully ported and
  smoke-tested (normalize/flatten, sqlite batch store, validator, and
  `load_row`'s logic up to the point of an actual QAD network call all run
  correctly). The other 9 entities are registered as `None` in
  `app/core/registry.py` — the API will respond with a clear "not yet ported"
  error if you try to validate/load them, rather than crashing.
- **`frontend/`** — structure guide + one generic API client only. I didn't
  have your actual `src/` contents, so nothing here overwrites real UI code.
- **`legacy/`** — put your current `Backend/Scripts/*` and old `main.py` here
  for reference while porting the rest.

## Running it

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# edit app/config.json with real QAD credentials (placeholders are in there now)
uvicorn app.main:app --reload --port 8000
```

Note: I couldn't pip-install fastapi/pydantic in this sandbox (no network),
so the API layer (`app/api/*`, `app/main.py`) is written carefully against
the same patterns as your existing main.py but hasn't been execution-tested
end-to-end the way the core logic (normalize/flatten/batch_store/Customer
validator+loader) has. Worth running `uvicorn app.main:app --reload` locally
and watching the startup output before pointing KNIME at it.

## What changed from your old main.py

- No more `.xlsx` files, no `Data/<Entity>/` folders, no file renaming
  (`error_*`) or archiving for entities going through this new path.
- `POST /api/upload-json` now creates a durable batch (sqlite) instead of
  writing an Excel file.
- `GET /api/batch/{id}` is new — returns the exact raw JSON as received,
  per requirement #12.
- `/api/validate` and `/api/load` now take `{"batch_ids": [...]}` instead of
  `{"entities": [...]}`, since one entity can have many pending batches.
- SSE event names changed from `entity_start/file_start/file_result/entity_result`
  to `batch_start/row_result/batch_result` — the frontend's event-stream
  parsing loop needs updating to match (the encoding itself, `data: {...}\r\n\r\n`,
  is unchanged).

## Next steps

1. Share one real `Supplier_Item` (or any other) KNIME payload so
   `COLUMN_ALIASES` for Customer (and the next entity) can be filled in for
   real instead of left empty.
2. Pick the next entity to port — ideally one where you also have the
   existing `validate_*.py` / `*_load.py` source, same as Customer.
3. Confirm React vs. something else for the frontend so `src/` can actually
   be built out instead of just described.
