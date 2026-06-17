"""
app/entities/customer/config.py
--------------------------------
Column mapping and defaults for Customer entity.

Input JSON comes directly with QAD field names (no cm_ prefix).
Some GL profile codes come as integer IDs; loader converts them to strings.

Business Relations are always created brand-new alongside the customer
(isCreateBusinessRelationRequired). Since the sender never provides
real BR codes or address data, those are hardcoded as defaults below.
"""

# Map input JSON column names to QAD customerV2s API field names
COLUMN_ALIASES = {
    # Primary key
    "CustomerCode": "customerCode",

    # Relation + Classification
    "businessRelationName": "businessRelationName",
    "customerTypeCode": "customerTypeCode",
    # NOTE: removed "BusinessRelation_ID": "businessRelationCode".
    # That treated an internal numeric ID as if it were a QAD code,
    # which QAD can't resolve -> caused the 500 errors.
    # businessRelationCode is now derived from customerCode in loader.py.

    # Credit & Payment Terms
    "creditTermsCode": "creditTermsCode",
    "isLockedCreditLimit": "isLockedCreditLimit",
    "highCredit": "highCredit",

    # GL Profiles (come as IDs, will be converted to strings)
    "InvControlGLProfile_ID": "invoiceControlGLProfileCode",
    "creditNoteControlGLProfileCode": "creditNoteControlGLProfileCode",
    "prePaymentControlGLProfileCode": "prePaymentControlGLProfileCode",
    "salesAccountGLProfileCode": "salesAccountGLProfileCode",

    # Invoice & Finance
    "invoiceControlGLProfileCode": "invoiceControlGLProfileCode",
    "isFinanceCharge": "isFinanceCharge",

    # Address & Location
    "commentNote": "commentNote",
    "stateCode": "stateCode",
    "taxZone": "taxZone",
    "billToCustomerCode": "billToCustomerCode",

    # Tax
    "isTaxable": "isTaxable",
    "isTaxIncluded": "isTaxIncluded",
    "taxClass": "taxClass",
    "federalTax": "federalTax",
    "stateTax": "stateTax",

    # Currency & Language
    "currencyCode": "currencyCode",
    "languageCode": "languageCode",

    # Shared Set
    "sharedSetCode": "sharedSetCode",

    # Balance
    "openItemBalance": "openItemBalance",

    # Ignored: internal IDs not sent to QAD
    # Debtor_ID, FinChgGLProfile_ID, Reason_ID
}

# Hardcoded defaults (applied if field is empty/missing)
DEFAULTS = {
    "invoiceStatusCode": "OK2PAY",
    "customCombo10": "B2B",
    "isOverruleAllowedSOCreditLimit": True,
    "domainCode": "10USA",
    "sharedSetCode": "QMI-CUST",

    # --- New: required so QAD creates a brand-new Business Relation
    # inline instead of trying to look one up by code ---
    "isCreateBusinessRelationRequired": True,
    "isBusinessRelationActive": True,
    "isActive": True,

    # --- New: hardcoded address info for the new BR, since the
    # sender never provides city/state/country for these records ---
    "city": "Manhattan",
    "stateCode": "NJ",
    "countryCode": "USA",
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