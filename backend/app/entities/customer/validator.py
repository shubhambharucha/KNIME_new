"""
app/entities/customer/validator.py
--------------------------------------
Ported from the existing validate.py (Document 2). Same FIELD_RULES checks,
but returns a list of error strings for ONE record instead of writing fills
into a workbook. No file I/O, no openpyxl.
"""

from app.entities.customer.config import FIELD_RULES, VALID_LOGICAL


def validate_row(record: dict) -> list[str]:
    """Returns a list of human-readable error strings; empty list = valid."""
    errors: list[str] = []

    for col_name, rule in FIELD_RULES.items():
        value = record.get(col_name)
        str_val = str(value).strip() if value is not None else ""
        is_empty = str_val == "" or str_val.lower() == "none"

        if is_empty:
            errors.append(f"{col_name}: empty")
            continue

        if rule["type"] == "logical":
            if str_val.lower() not in VALID_LOGICAL:
                errors.append(f"{col_name}: must be Yes or No (got '{str_val}')")
            continue

        max_len = rule.get("max_len")
        if max_len and len(str_val) > max_len:
            errors.append(f"{col_name}: max {max_len} chars (got {len(str_val)})")

    return errors
