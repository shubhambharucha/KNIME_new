"""
app/entities/customer/config.py
--------------------------------
Column mapping and defaults for Customer entity.

Input JSON comes directly with QAD field names (no cm_ prefix).
Some GL profile codes come as integer IDs; loader converts them to strings.
"""

# Map input JSON column names to QAD customerV2s API field names
# Most fields use their QAD names directly; ID fields are renamed/mapped
COLUMN_ALIASES = {
    # Primary key
    "CustomerCode": "customerCode",
    
    # Relation + Classification
    "businessRelationName": "businessRelationName",
    "BusinessRelation_ID": "businessRelationCode",  # Use ID as code
    "customerTypeCode": "customerTypeCode",
    
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
    "sharedSetCode": "QMI-CUST",  # Default shared set if empty
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