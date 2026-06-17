"""
app/entities/customer/config.py
----------------------------------
Mandatory columns ported directly from Customer_load.py.

COLUMN_ALIASES is the explicit, declared semantic mapping the doc's "flexible
key matching" idea is replaced with — if KNIME's field names differ from QAD's
internal names below, list the mapping here. Left empty until you share a real
KNIME Customer payload; nothing is guessed.
"""

MANDATORY_COLUMNS = [
    "Customer",
    "Shared Set",
    "Business Relation",
    "Active",
    "Currency",
    "Credit Terms",
    "Invoice Status",
    "Invoice Control GL Profile",
    "Credit Note Control GL Profile",
    "Prepayment Control GL Profile",
    "Sales Account GL Profile",
]

MANDATORY_DOMAIN_COLUMNS = [
    "Domain",
    "Site Code",
    "Daybook Set",
]

FIELD_RULES = {
    "Customer":            {"type": "character", "max_len": 8},
    "Shared Set":          {"type": "character", "max_len": 20},
    "Business Relation":   {"type": "character", "max_len": 20},
    "Active":              {"type": "logical",   "max_len": None},
    "Currency":            {"type": "character", "max_len": 3},
    "Credit Terms":        {"type": "character", "max_len": 8},
    "Invoice Status":      {"type": "character", "max_len": 20},
    "Invoice Control GL Profile": {"type": "character", "max_len": 20},
    "Credit Note Control GL Profile": {"type": "character", "max_len": 20},
    "Prepayment Control GL Profile": {"type": "character", "max_len": 20},
    "Sales Account GL Profile": {"type": "character", "max_len": 20},
}

VALID_LOGICAL = {"yes", "no"}

# KNIME column name -> internal name used by FIELD_RULES / build_payload above.
# e.g. "CUST_CODE": "Customer"
COLUMN_ALIASES: dict[str, str] = {}

# Injected into every record before validation/load if missing, e.g. {"Domain Code": "10USA"}
DEFAULTS: dict[str, str] = {}
