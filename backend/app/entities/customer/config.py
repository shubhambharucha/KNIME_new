"""
app/entities/customer/config.py
"""

# All fields extracted from incoming JSON mapped to their QAD payload names.
# Order matches the confirmed-working payload exactly.
PAYLOAD_FIELDS = {
    "customerCode":                   "customerCode",
    "businessRelationCode":           "businessRelationCode",
    "customerTypeCode":               "customerTypeCode",
    "creditTermsCode":                "creditTermsCode",
    "invoiceControlGLProfileCode":    "invoiceControlGLProfileCode",
    "creditNoteControlGLProfileCode": "creditNoteControlGLProfileCode",
    "prePaymentControlGLProfileCode": "prePaymentControlGLProfileCode",
    "salesAccountGLProfileCode":      "salesAccountGLProfileCode",
    "invoiceStatusCode":              "invoiceStatusCode",
    "addressSearchName":              "addressSearchName",
    "city":                           "city",
    "stateCode":                      "stateCode",
    "businessRelationName":           "businessRelationName",
    "addressName":                    "addressName",
    "currencyCode":                   "currencyCode",
    "customerCurrencyCode":           "customerCurrencyCode",
    "languageCode":                   "languageCode",
    "taxZone":                        "taxZone",
    "customCombo10":                  "customCombo10",
}

# Never sourced from incoming JSON — always injected as-is.
HARDCODED = {
    "sharedSetCode":                    "QMI-CUST",
    "isOverruleAllowedSOCreditLimit":   True,
    "isCreateBusinessRelationRequired": True,
}

# Must be present and non-empty after assembly or the row is rejected.
MANDATORY_FIELDS = [
    "customerCode",
    "businessRelationCode",
    "currencyCode",
    "sharedSetCode",
    "creditTermsCode",
    "invoiceControlGLProfileCode",
    "creditNoteControlGLProfileCode",
    "prePaymentControlGLProfileCode",
    "salesAccountGLProfileCode",
    "invoiceStatusCode",
]