"""
app/core/normalize.py
----------------------
Two purely STRUCTURAL transforms — no semantic field-name guessing here.
Semantic mapping (KNIME field name -> QAD field name) is a separate, explicit
step that lives in entities/<name>/config.py (COLUMN_ALIASES), so it's always
visible and reviewable rather than inferred.

normalize(): coerce arbitrary incoming JSON into a flat list[dict] of records.
flatten():   collapse nested dicts into dotted/underscored single-level keys.
"""

from typing import Any


def normalize(raw: Any) -> list[dict]:
    """
    Accepts whatever JSON shape arrived and returns a list of record dicts.
    Never raises and never rejects — per the "accept all input" design rule.
    """
    if raw is None:
        return []

    if isinstance(raw, list):
        return [r if isinstance(r, dict) else {"value": r} for r in raw]

    if isinstance(raw, dict):
        # Common KNIME shape: {"entity": "...", "data": [...]}
        for key in ("data", "rows", "records", "items"):
            value = raw.get(key)
            if isinstance(value, list):
                return [r if isinstance(r, dict) else {"value": r} for r in value]
        # No recognizable list field — treat the whole object as one record
        return [raw]

    # Bare scalar/string/number payload
    return [{"value": raw}]


def flatten(record: dict, parent_key: str = "", sep: str = "_") -> dict:
    """
    {"item": {"details": {"supplier": "SG262"}}} -> {"item_details_supplier": "SG262"}

    Nested dicts are flattened. Lists are left as-is (flattening list indices
    tends to produce noisy, unstable keys and rarely matches anything QAD expects);
    if a specific entity needs list-flattening later, that's a deliberate addition
    to that entity's own preprocessing, not a generic behavior.
    """
    out: dict = {}
    for key, value in record.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else str(key)
        if isinstance(value, dict):
            out.update(flatten(value, new_key, sep=sep))
        else:
            out[new_key] = value
    return out
