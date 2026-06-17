"""
app/entities/customer/config.py
--------------------------------
Customer entity configuration.

Two fields are extracted from the incoming JSON:
  - CustomerCode  →  customerCode
  - currencyCode  →  currencyCode

Everything else is dropped. The rest of the payload is built from
DEFAULTS, with a handful of fields derived from customerCode at runtime
(businessRelationCode, businessRelationName) — that derivation happens
in the loader, not here.
"""

# The only two fields we care about from the incoming record.
# Key = incoming JSON field name, Value = canonical name used in payload.
EXTRACT_FIELDS = {
    "CustomerCode": "customerCode",
    "currencyCode": "currencyCode",
}

# Hardcoded values applied to every record after extraction.
# Copied exactly from the confirmed-working minimal payload.
DEFAULTS: dict = {
    # Identity
    "customerTypeCode": "INTC",
    "sharedSetCode": "QMI-CUST",
    "languageCode": "us",

    # AR GL profiles
    "invoiceControlGLProfileCode": "ARcontrol3rdparty",
    "creditNoteControlGLProfileCode": "ARcontrol3rdparty",
    "prePaymentControlGLProfileCode": "ARcontrol3rdparty",
    "salesAccountGLProfileCode": "FinCharge1",

    # Terms & status
    "creditTermsCode": "1M",
    "invoiceStatusCode": "C-OK",

    # Tax
    "taxZone": "USA-NJ",
    "vatDeliveryType": "SERVICE",

    # Business Relation — create new inline, no lookup
    "isCreateBusinessRelationRequired": True,
    "isBusinessRelationActive": True,
    "isActive": True,

    # Address (hardcoded, same as working payload)
    "addressName": "default",
    "addressSearchName": "default",
    "addressTypeCode": "HEADOFFICE",
    "city": "Manhattan",
    "countryCode": "USA",
}

# Fields that must be present and non-empty before we POST.
MANDATORY_FIELDS = [
    "customerCode",
    "currencyCode",
    "businessRelationCode",
    "businessRelationName",
    "sharedSetCode",
    "creditTermsCode",
    "invoiceControlGLProfileCode",
    "creditNoteControlGLProfileCode",
    "prePaymentControlGLProfileCode",
    "salesAccountGLProfileCode",
    "invoiceStatusCode",
]