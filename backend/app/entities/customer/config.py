"""
app/entities/customer/config.py
--------------------------------
Column mapping and defaults for Customer entity.

COLUMN_ALIASES: Input JSON field → QAD API field
DEFAULTS: Hardcoded values applied to every customer
MANDATORY_COLUMNS: Required fields for payload validation
"""

# Map input JSON column names to QAD customerV2s API field names
# NOTE: cm_addr is used for both customerCode and businessRelationCode
#       The loader will copy customerCode → businessRelationCode if not explicitly provided
COLUMN_ALIASES = {
    "cm_addr": "customerCode",
    "cm_type": "customerTypeCode",
    "cm_cr_terms": "creditTermsCode",
    "cm_fin": "isFinanceCharge",
    "cm_ar_acct": "invoiceControlGLProfileCode",
    "cm_rmks": "commentNote",
    "cm_region": "stateCode",
    "cm_sort": "businessRelationName",
    "cm_balance": "openItemBalance",
    "cm_taxable": "isTaxable",
    "cm_curr": "currencyCode",
    "cm_lang": "languageCode",
    "cm_db": "sharedSetCode",
    "cm_cr_hold": "isLockedCreditLimit",
    "cm_high_cr": "highCredit",
    "cm_high_date": "highCreditDate",
    "cm_sale_date": "lastSaleDate",
    "cm_fst_id": "federalTax",
    "cm_pst_id": "stateTax",
    "cm_tax_in": "isTaxIncluded",
    "cm_class": "taxClass",
    "cm_taxc": "taxZone",
    "cm_bill": "billToCustomerCode",
}

# Hardcoded defaults (always applied, can be overridden by input)
DEFAULTS = {
    "creditNoteControlGLProfileCode": "ARcontrol3rdparty",
    "prePaymentControlGLProfileCode": "ARcontrol3rdparty",
    "salesAccountGLProfileCode": "Sales",
    "invoiceStatusCode": "OK2PAY",
    "customCombo10": "B2B",
    "isOverruleAllowedSOCreditLimit": True,
    "domainCode": "10USA",
    # Address fields populated from customerCode/businessRelationName
    "addressName": None,  # Will be set from businessRelationName
    "addressSearchName": None,  # Will be set from businessRelationName
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