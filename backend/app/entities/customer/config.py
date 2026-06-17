"""
app/entities/customer/config.py
--------------------------------
Column mapping and defaults for Customer entity.

STRICT MODE:
Only `CustomerCode` and `currencyCode` are read from the incoming
record. Every other incoming field is dropped at the aliasing step.
All other values are hardcoded in DEFAULTS to match the confirmed-
working minimal payload for QAD customerV2s (creating a new Business
Relation inline).
"""

# Whitelist: only these two survive aliasing. Everything else in the
# source JSON (Debtor_ID, InvControlGLProfile_ID, BusinessRelation_ID,
# businessRelationName, taxZone, creditTermsCode, etc.) is dropped
# before it ever reaches load_batch() — those values don't exist in
# this environment and were causing the 500s.
COLUMN_ALIASES = {
    "CustomerCode": "customerCode",
    "currencyCode": "currencyCode",
}

# Hardcoded values applied to every record (the confirmed minimal
# working payload, copied as-is).
DEFAULTS = {
    "customerTypeCode": "INTC",
    "creditTermsCode": "1M",
    "invoiceStatusCode": "C-OK",
    "invoiceControlGLProfileCode": "ARcontrol3rdparty",
    "creditNoteControlGLProfileCode": "ARcontrol3rdparty",
    "prePaymentControlGLProfileCode": "ARcontrol3rdparty",
    "salesAccountGLProfileCode": "FinCharge1",
    "taxZone": "USA",
    "sharedSetCode": "QMI-CUST",

    # Tells QAD to create the Business Relation inline rather than
    # look one up by code (none of these BR codes exist in this env).
    "isCreateBusinessRelationRequired": True,
    "isBusinessRelationActive": True,
    "isActive": True,

    # Address fields for the new Business Relation.
    "city": "Manhattan",
    "countryCode": "USA",
    "addressSearchName": "Lannister row",
}

# Mandatory fields for payload validation
MANDATORY_COLUMNS = [
    "customerCode",
    "businessRelationCode",
    "creditTermsCode",
    "invoiceControlGLProfileCode",
    "creditNoteControlGLProfileCode",
    "prePaymentControlGLProfileCode",
    "salesAccountGLProfileCode",
    "invoiceStatusCode",
    "currencyCode",
    "sharedSetCode",
]