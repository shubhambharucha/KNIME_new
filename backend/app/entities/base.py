"""
app/entities/base.py
----------------------
Small helpers shared across every entity. Kept tiny on purpose — entity-specific
logic belongs in that entity's own validator.py / loader.py, not here.
"""


def val(record: dict, col: str) -> str:
    v = record.get(col)
    return str(v).strip() if v is not None else ""


def check_mandatory(record: dict, columns: list[str]) -> list[str]:
    missing = []
    for col in columns:
        v = record.get(col)
        if v is None or str(v).strip() == "" or str(v).strip().lower() == "none":
            missing.append(col)
    return missing
