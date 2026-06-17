"""
app/entities/customer/config.py
"""

# Single flat payload — fields sourced from incoming JSON are mapped by name.
# Fields marked # hardcoded are always sent as-is; loader will use their value directly.
PAYLOAD_FIELDS = {
    # ── Fields sourced from incoming JSON ─────────────────────────────────
    "uri": f"urn:be:com.qad.base.customer.ICustomerV2:{"QMI-CUST"}.{"TANVI01"}",
    "isBusinessRelationActive": True,
    "BusinessRelationID": "",
    "changeStatus": "2",  # hardcoded as you requested
    "dataOperation": "",
    "concurrencyHash": "",
    "disallowedActions": "",
    "disallowedActionsMessage": "",
    "isPredefaulted": "",
    "isDomainRestricted": "",
    "customerCode":                    "customerCode",
    "businessRelationCode":            "businessRelationCode",
    "customerTypeCode":                "customerTypeCode",
    "creditTermsCode":                 "creditTermsCode",
    "invoiceControlGLProfileCode":     "invoiceControlGLProfileCode",
    "creditNoteControlGLProfileCode":  "creditNoteControlGLProfileCode",
    "prePaymentControlGLProfileCode":  "prePaymentControlGLProfileCode",
    "salesAccountGLProfileCode":       "salesAccountGLProfileCode",
    "invoiceStatusCode":               "invoiceStatusCode",
    "addressSearchName":               "addressSearchName",
    "addressName":                     "addressName",
    "city":                            "city",
    "stateCode":                       "stateCode",
    #"businessRelationName":            "businessRelationName",
    "currencyCode":                    "currencyCode",
    #"customerCurrencyCode":            "customerCurrencyCode",
    "languageCode":                    "languageCode",
    "taxZone":                         "taxZone",

    # ── Hardcoded / defaulted fields (exact copy from working payload) ─────
    "businessRelationName":                "",
    "customerCurrencyCode":           "USD",
    "customerIsInclDeduction":        True,  # hardcoded — present in working payload
    "accruedRevRecGLProfileCode":          "",                    # hardcoded
    "accruedRevRecGLProfileDesc":          "",                    # hardcoded
    "accruedRevRecGLProfileID":            0,                     # hardcoded
    "addressTypeCode":                     "HEADOFFICE",          # hardcoded
    "billCollectorCode":                   "",                    # hardcoded
    "billCollectorID":                     0,                     # hardcoded
    "billingScheduleCode":                 "",                    # hardcoded
    "billingScheduleDescription":          "",                    # hardcoded
    "billingScheduleID":                   0,                     # hardcoded
    "billToCustomerCode":                  "",                    # hardcoded
    "billToCustomerID":                    0,                     # hardcoded
    "COGSAccruedRevRecGLProfileCode":      "",                    # hardcoded
    "COGSAccruedRevRecGLProfileDesc":      "",                    # hardcoded
    "COGSAccruedRevRecGLProfileID":        0,                     # hardcoded
    "COGSDeferredRevRecGLProfileCode":     "",                    # hardcoded
    "COGSDeferredRevRecGLProfileDesc":     "",                    # hardcoded
    "COGSDeferredRevRecGLProfileID":       0,                     # hardcoded
    "COGSOffsetRevRecGLProfileCode":       "",                    # hardcoded
    "COGSOffsetRevRecGLProfileDesc":       "",                    # hardcoded
    "COGSOffsetRevRecGLProfileID":         0,                     # hardcoded
    #"commentNote":                         "",                    # hardcoded
    #"corporateGroupCode":                  "",                    # hardcoded
    #"corporateGroupDescription":           "",                    # hardcoded
    #"corporateGroupID":                    0,                     # hardcoded
    "countryCode":                         "USA",                 # hardcoded
    #"countryDescription":                  "USA - TAX PURPOSE",   # hardcoded
    #"countyCode":                          "",                    # hardcoded
    #"countyDescription":                   "",                    # hardcoded
    #"creditAgencyReference":               "",                    # hardcoded
    #"creditRatingCode":                    "",                    # hardcoded
    #"creditRatingID":                      0,                     # hardcoded
    #"creditTermsType":                     "NORMAL",              # hardcoded
    #"currencyDescription":                 "US Dollar",           # hardcoded
    #"currencyID":                          923,                   # hardcoded
    "domiciliationNumber":                 0,                     # hardcoded
    "EMail":                               "",                    # hardcoded
    "EORINumber":                          "",                    # hardcoded
    #"fax":                                 "",                    # hardcoded
    #"federalTax":                          "",                    # hardcoded
    #"financeChargeGLProfileCode":          "",                    # hardcoded
    #"financeChargeGLProfileDesc":          "",                    # hardcoded
    #"financeChargeGLProfileID":            0,                     # hardcoded
    #"fixedCreditLimit":                    0,                     # hardcoded
    #"highCredit":                          0,                     # hardcoded
    #"intercompanyCode":                    "",                    # hardcoded
    #"invoiceStatusDescription":            "Customer Invoice OK", # hardcoded
    #"invoiceStatusID":                     113626,                # hardcoded
    "isActive":                            True,                  # hardcoded
    "isAutoCreateRevRecContracts":         False,                 # hardcoded
    "isBusinessRelationActive":            True,                  # hardcoded
    "isBusinessRelationFieldsEnabled":     True,                  # hardcoded
    "isBusinessRelationIntercompany":      False,                 # hardcoded
    "isCheckAfterInvoiceCreditLimit":      False,                 # hardcoded
    "isCheckAfterSOCreditLimit":           False,                 # hardcoded
    "isCheckBeforeInvoiceCreditLimit":     False,                 # hardcoded
    "isCheckBeforeSOCreditLimit":          False,                 # hardcoded
    "isCompensationAllowed":              False,                  # hardcoded
    "isCreateBusinessRelationRequired":    True,                  # hardcoded
    "isDomainRestricted":                  False,                 # hardcoded
    "isElectronicInvoiceIN":              False,                  # hardcoded
    "isFinanceCharge":                     False,                 # hardcoded
    "isFixedCreditLimit":                  False,                 # hardcoded
    "isIncludeDraftCreditLimit":           False,                 # hardcoded
    "isIncludeOpenItemsCreditLimit":       False,                 # hardcoded
    "isIncludeSOCheckCreditLimit":         False,                 # hardcoded
    "isInternalEntity":                    False,                 # hardcoded
    "isInvoiceByAuthorization":            False,                 # hardcoded
    "isLastFiling":                        False,                 # hardcoded
    "isLockedCreditLimit":                 False,                 # hardcoded
    "isMaxDaysOverdueCreditLimit":         False,                 # hardcoded
    "isOverAllowedInvoiceCreditLimit":     False,                 # hardcoded
    "isOverruleAllowedSOCreditLimit":      True,                  # hardcoded
    "isPredefaulted":                      False,                 # hardcoded
    "isPrintBillWithItemDetails":          False,                 # hardcoded
    "isPrintReminder":                     False,                 # hardcoded
    "isPrintStatement":                    False,                 # hardcoded
    "isReminderRequired":                  False,                 # hardcoded
    "isReportedIN":                        False,                 # hardcoded
    "isTaxable":                           True,                  # hardcoded
    "isTaxInCity":                         True,                  # hardcoded
    "isTaxIncluded":                       False,                 # hardcoded
    "isTaxReport":                         False,                 # hardcoded
    "isTemporaryAddress":                  False,                 # hardcoded
    "isToBeLockedCreditLimit":             False,                 # hardcoded
    "isToleranceFromOwnBank":              False,                 # hardcoded
    "isTurnOverCreditLimit":               False,                 # hardcoded
    "isWithPreInvoiceGroup":               False,                 # hardcoded
    #"languageDescription":                 "english (U.S.)",      # hardcoded
    #"latitude":                            0,                     # hardcoded
    #"longitude":                           0,                     # hardcoded
    #"maxDaysCreditLimit":                  0,                     # hardcoded
    "miscellaneousTax1":                   "",                    # hardcoded
    "miscellaneousTax2":                   "",                    # hardcoded
    "miscellaneousTax3":                   "",                    # hardcoded
    "nameControl":                         "",                    # hardcoded
    #"overToleranceAmount":                 0,                     # hardcoded
    #"overTolerancePercent":                0,                     # hardcoded
    "paymentGroupCode":                    "",                    # hardcoded
    #"paymentGroupDescription":             "",                    # hardcoded
    #"paymentGroupID":                      0,                     # hardcoded
    #"postalFormat":                        "0",                   # hardcoded
    "sharedSetCode":                       "QMI-CUST",            # hardcoded
    #"sharedSetID":                         217972,                # hardcoded
    "shortToleranceAmount":                0,                     # hardcoded
    "shortTolerancePercent":               0,                     # hardcoded
    #"stateDescription":                    "New York",            # hardcoded
    "statementCycle":                      "",                    # hardcoded
    "stateTax":                            "",                    # hardcoded
    "street1":                             "",                    # hardcoded
    "street2":                             "",                    # hardcoded
    "street3":                             "",                    # hardcoded
    "subAccountProfileCode":               "",                    # hardcoded
    "subAccountProfileDesc":               "",                    # hardcoded
    "subAccountProfileID":                 0,                     # hardcoded
    "taxClass":                            "",                    # hardcoded
    "taxClassDescription":                 "",                    # hardcoded
    "taxDeclaration":                      0,                     # hardcoded
    "taxUsage":                            "",                    # hardcoded
    "taxUsageDescription":                 "",                    # hardcoded
    "taxZoneDescription":                  "",                    # hardcoded
    "telephone":                           "",                    # hardcoded
    "toleranceAt":                         "PAYMENT LEVEL",       # hardcoded
    #"totalDaysLate":                       0,                     # hardcoded
    #"totalNumberOfInvoices":               0,                     # hardcoded
    #"turnoverCreditLimitPercent":          0,                     # hardcoded
    "vatDeliveryType":                     "SERVICE",             # hardcoded
    "vatPercentageLevel":                  "NONE",                # hardcoded
    "warningCreditLimitPercent":           0,                     # hardcoded
    "webSite":                             "",                    # hardcoded
    "zipCode":                             "",                    # hardcoded
    #"bankNumberRefV2s":                    [],                    # hardcoded
    #"customerContactV2s":                  [],                    # hardcoded
    #"customerSafDefaultV2s":               [],                    # hardcoded
    #"MDMBankNrSharedSets":                 [],                    # hardcoded
    #"reminderCustContactV2s":              [],                    # hardcoded
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