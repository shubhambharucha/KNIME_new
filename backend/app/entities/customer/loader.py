"""
app/entities/customer/loader.py
-----------------------------------
Ported from Customer_load.py. build_payload(), post_customer(), get_customer(),
get_mfg_customer(), post_mfg_customer() are carried over essentially unchanged —
they only ever operated on dicts, never on the workbook.

What's gone: openpyxl, PatternFill, process_file(), run(), the entire
xlsx-rename/archive flow, and the for-loop-over-files orchestration.
What's new: load_row(), the single-row entry point the API layer calls —
this is process_file()'s per-row body, with wb.save() calls removed and
fill/highlight side effects removed (errors are returned as strings instead).

CREATE flow (Data Operation = C):
  1. POST to customerV2s  -> creates customer
  2. GET  mfgCustomers    -> fetch auto-created domain record
  3. PATCH + POST         -> update siteCode + daybookSetCode

UPDATE flow (Data Operation = U):
  1. GET  customerV2s     -> fetch existing record
  2. Patch editable fields
  3. POST customerV2s     -> update customer
"""

import requests

from app.config import CONFIG
from app.entities.base import check_mandatory, val
from app.entities.customer.config import MANDATORY_COLUMNS, MANDATORY_DOMAIN_COLUMNS
from app.qad.auth import TokenExpired, TokenManager


# =============================================================================
# PAYLOAD BUILDER  (full payload — every field visible, unchanged from original)
# =============================================================================

def build_payload(row: dict) -> dict:
    def v(col: str) -> str:
        return val(row, col)

    customer_code = v("Customer")
    shared_set = v("Shared Set")
    uri = f"urn:be:com.qad.base.customer.ICustomerV2:{shared_set}.{customer_code}"

    return {
        "supplementaryMessages": [],
        "customerV2s": [
            {
                "uri": uri,
                "instanceURI": uri,
                "customerCode": customer_code,
                "customerID": 0,
                "sharedSetCode": shared_set,
                "sharedSetID": 0,
                "businessRelationCode": v("Business Relation"),
                "businessRelationID": 0,
                "businessRelationName": "",
                "businessRelationName2": "",
                "businessRelationName3": "",
                "businessRelationConcurrencyHash": "",
                "isBusinessRelationActive": True,
                "isBusinessRelationFieldsEnabled": True,
                "isBusinessRelationIntercompany": False,
                "isCreateBusinessRelationRequired": True,
                "isInternalEntity": False,
                "intercompanyCode": "",
                "addressID": 0,
                "addressName": v("Name"),
                "addressSearchName": v("Search Name"),
                "addressTypeCode": v("Address Type"),
                "addressConcurrencyHash": "",
                "street1": v("Address 1"),
                "street2": v("Address 2"),
                "street3": "",
                "city": v("City"),
                "cityCode": "",
                "zipCode": v("Postal Code"),
                "stateCode": v("State"),
                "stateDescription": "",
                "stateTax": "",
                "countryCode": v("Country"),
                "countryDescription": "",
                "countyCode": "",
                "countyDescription": "",
                "postalFormat": "0",
                "latitude": 0,
                "longitude": 0,
                "isTemporaryAddress": False,
                "changeStatus": "2",
                "dataOperation": "",
                "concurrencyHash": "",
                "disallowedActions": "",
                "disallowedActionsMessage": "",
                "isPredefaulted": False,
                "isDomainRestricted": False,
                "lastModifiedDate": "",
                "lastModifiedTime": 0,
                "lastModifiedUser": "",
                "isActive": v("Active").lower() == "yes",
                "customerTypeCode": v("Customer Type"),
                "customerTypeID": 0,
                "currencyCode": v("Currency"),
                "currencyDescription": "",
                "currencyID": 0,
                "customerCurrencyCode": v("Currency"),
                "languageCode": v("Language"),
                "languageDescription": "",
                "creditTermsCode": v("Credit Terms"),
                "creditTermsDescription": "",
                "creditTermsID": 0,
                "creditTermsType": "",
                "invoiceStatusCode": v("Invoice Status"),
                "invoiceStatusDescription": "",
                "invoiceStatusID": 0,
                "isInvoiceByAuthorization": False,
                "isWithPreInvoiceGroup": False,
                "isPrintBillWithItemDetails": False,
                "invoiceControlGLProfileCode": v("Invoice Control GL Profile"),
                "invoiceControlGLProfileDesc": "",
                "invoiceControlGLProfileID": 0,
                "creditNoteControlGLProfileCode": v("Credit Note Control GL Profile"),
                "creditNoteControlGLProfileDesc": "",
                "creditNoteControlGLProfileID": 0,
                "prePaymentControlGLProfileCode": v("Prepayment Control GL Profile"),
                "prePaymentControlGLProfileDesc": "",
                "prePaymentControlGLProfileID": 0,
                "salesAccountGLProfileCode": v("Sales Account GL Profile"),
                "salesAccountGLProfileDesc": "",
                "salesAccountGLProfileID": 0,
                "deductionControlGLProfileCode": "",
                "deductionControlGLProfileDesc": "",
                "deductionControlGLProfileID": 0,
                "financeChargeGLProfileCode": "",
                "financeChargeGLProfileDesc": "",
                "financeChargeGLProfileID": 0,
                "accruedRevRecGLProfileCode": "",
                "accruedRevRecGLProfileDesc": "",
                "accruedRevRecGLProfileID": 0,
                "deferredRevRecGLProfileCode": "",
                "deferredRevRecGLProfileDesc": "",
                "deferredRevRecGLProfileID": 0,
                "COGSAccruedRevRecGLProfileCode": "",
                "COGSAccruedRevRecGLProfileDesc": "",
                "COGSAccruedRevRecGLProfileID": 0,
                "COGSDeferredRevRecGLProfileCode": "",
                "COGSDeferredRevRecGLProfileDesc": "",
                "COGSDeferredRevRecGLProfileID": 0,
                "COGSOffsetRevRecGLProfileCode": "",
                "COGSOffsetRevRecGLProfileDesc": "",
                "COGSOffsetRevRecGLProfileID": 0,
                "isAutoCreateRevRecContracts": False,
                "revRecRuleID": 0,
                "reviewRequiredForContracts": "",
                "taxZone": v("Tax Zone"),
                "taxZoneDescription": "",
                "taxClass": "",
                "taxClassDescription": "",
                "taxDeclaration": 0,
                "taxUsage": "",
                "taxUsageDescription": "",
                "isTaxable": True,
                "isTaxInCity": True,
                "isTaxIncluded": False,
                "isTaxReport": False,
                "isLastFiling": False,
                "isReportedIN": False,
                "isElectronicInvoiceIN": False,
                "federalTax": "",
                "miscellaneousTax1": "",
                "miscellaneousTax2": "",
                "miscellaneousTax3": "",
                "customerGTVatTransType": "",
                "vatDeliveryType": "",
                "vatPercentageLevel": "",
                "nameControl": "",
                "EORINumber": "",
                "fixedCreditLimit": float(v("Fixed Credit Limit") or 0),
                "highCredit": 0,
                "isFixedCreditLimit": True,
                "isLockedCreditLimit": v("Credit Hold").lower() == "yes",
                "isToBeLockedCreditLimit": False,
                "isOverruleAllowedSOCreditLimit": True,
                "isCheckBeforeSOCreditLimit": False,
                "isCheckAfterSOCreditLimit": False,
                "isCheckBeforeInvoiceCreditLimit": False,
                "isCheckAfterInvoiceCreditLimit": False,
                "isOverAllowedInvoiceCreditLimit": False,
                "isIncludeDraftCreditLimit": False,
                "isIncludeOpenItemsCreditLimit": True,
                "isIncludeSOCheckCreditLimit": False,
                "isMaxDaysOverdueCreditLimit": False,
                "isTurnOverCreditLimit": False,
                "maxDaysCreditLimit": 0,
                "overToleranceAmount": 0,
                "overTolerancePercent": 0,
                "shortToleranceAmount": 0,
                "shortTolerancePercent": 0,
                "warningCreditLimitPercent": 0,
                "turnoverCreditLimitPercent": 0,
                "totalDaysLate": 0,
                "totalNumberOfInvoices": 0,
                "creditRatingCode": v("Credit Rating"),
                "creditRatingID": 0,
                "creditAgencyReference": "",
                "isFinanceCharge": False,
                "isPrintReminder": False,
                "isReminderRequired": False,
                "isPrintStatement": False,
                "reminderCountReset": False,
                "reminderAddressChangeStatus": "",
                "reminderAddressID": 0,
                "reminderAddressTypeCode": "",
                "reminderCustContactV2s": [],
                "paymentGroupCode": "",
                "paymentGroupDescription": "",
                "paymentGroupID": 0,
                "domiciliationNumber": 0,
                "isToleranceFromOwnBank": False,
                "isCompensationAllowed": False,
                "billToCustomerCode": "",
                "billToCustomerID": 0,
                "billCollectorCode": "",
                "billCollectorID": 0,
                "billingScheduleCode": "",
                "billingScheduleDescription": "",
                "billingScheduleID": 0,
                "statementCycle": "",
                "subAccountProfileCode": "",
                "subAccountProfileDesc": "",
                "subAccountProfileID": 0,
                "corporateGroupCode": "",
                "corporateGroupDescription": "",
                "corporateGroupID": 0,
                "EMail": v("Email"),
                "fax": "",
                "telephone": v("Telephone"),
                "webSite": "",
                "commentNote": "",
                "customerIsInclDeduction": False,
                "customShort0": "", "customShort1": "", "customShort2": "",
                "customShort3": "", "customShort4": "", "customShort5": "",
                "customShort6": "", "customShort7": "", "customShort8": "",
                "customShort9": "", "customShort10": "", "customShort11": "",
                "customShort12": "", "customShort13": "", "customShort14": "",
                "customShort15": "", "customShort16": "", "customShort17": "",
                "customShort18": "", "customShort19": "",
                "customLong0": "", "customLong1": "",
                "customNote": "",
                "customCombo0": "", "customCombo1": "", "customCombo2": "",
                "customCombo3": "", "customCombo4": "", "customCombo5": "",
                "customCombo6": "", "customCombo7": "", "customCombo8": "",
                "customCombo9": "", "customCombo10": "", "customCombo11": "",
                "customCombo12": "", "customCombo13": "", "customCombo14": "",
                "customDecimal0": 0, "customDecimal1": 0, "customDecimal2": 0,
                "customDecimal3": 0, "customDecimal4": 0,
                "customInteger0": 0, "customInteger1": 0, "customInteger2": 0,
                "customInteger3": 0, "customInteger4": 0,
                "customerContactV2s": [],
                "customerSafDefaultV2s": [],
                "bankNumberRefV2s": [],
                "MDMBankNrSharedSets": [],
            }
        ],
    }


# =============================================================================
# CUSTOMER API  (unchanged from Customer_load.py)
# =============================================================================

def post_customer(payload: dict, token: str, is_create: bool = False) -> tuple[bool, str]:
    customer = payload["customerV2s"][0]
    shared_set = customer.get("sharedSetCode", "")
    customer_code = customer.get("customerCode", "")

    if is_create:
        url = (
            f"{CONFIG['qad']['base_url']}/api/erp/customerV2s"
            f"?viewUri=urn:be:com.qad.base.customer.ICustomerV2"
        )
    else:
        url = (
            f"{CONFIG['qad']['base_url']}/api/erp/customerV2s"
            f"?sharedSetCode={shared_set}&customerCode={customer_code}"
            f"&viewUri=urn:be:com.qad.base.customer.ICustomerV2"
        )

    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )

    if resp.status_code == 401:
        raise TokenExpired()

    resp_json = resp.json()
    submit = resp_json.get("submitResult", {})

    if submit.get("success") is True:
        return True, ""

    errors = submit.get("errors", [])
    error_msg = "; ".join(
        e.get("message", "").strip() for e in errors if e.get("message", "").strip()
    ) or f"HTTP {resp.status_code} — submitResult.success was not True"

    return False, error_msg


def get_customer(shared_set: str, customer_code: str, token: str) -> dict:
    url = f"{CONFIG['qad']['base_url']}/api/erp/customerV2s"
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        params={
            "sharedSetCode": shared_set,
            "customerCode": customer_code,
            "viewUri": "urn:be:com.qad.base.customer.ICustomerV2",
        },
        timeout=30,
    )
    return resp.json()


def get_mfg_customer(domain: str, customer_code: str, token: str) -> dict:
    url = f"{CONFIG['qad']['base_url']}/api/erp/mfgCustomers"
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        params={
            "domainContext": domain,
            "customerCode": customer_code,
            "viewUri": "urn:be:com.qad.base.customer.IMfgCustomer",
        },
        timeout=30,
    )
    if resp.status_code == 401:
        raise TokenExpired()
    return resp.json()


def post_mfg_customer(payload: dict, domain: str, customer_code: str, token: str) -> tuple[bool, str]:
    url = (
        f"{CONFIG['qad']['base_url']}/api/erp/mfgCustomers"
        f"?domainContext={domain}&customerCode={customer_code}"
        f"&viewUri=urn:be:com.qad.base.customer.IMfgCustomer"
    )
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    if resp.status_code == 401:
        raise TokenExpired()

    resp_json = resp.json()
    submit = resp_json.get("submitResult", {})

    if submit.get("success") is True:
        return True, ""

    errors = submit.get("errors", [])
    error_msg = "; ".join(
        e.get("message", "").strip() for e in errors if e.get("message", "").strip()
    ) or f"HTTP {resp.status_code} — submitResult.success was not True"

    return False, error_msg


def update_domain_settings(
    customer_code: str, domain: str, site_code: str, daybook_set: str, token: str
) -> tuple[bool, str]:
    existing = get_mfg_customer(domain, customer_code, token)
    mfg_list = existing.get("data", {}).get("mfgCustomers") or existing.get("mfgCustomers")

    if not mfg_list:
        return False, f"Domain settings record not found for customer '{customer_code}' in domain '{domain}'"

    payload = existing.get("data", existing)
    mfg_record = mfg_list[0]
    mfg_record["siteCode"] = site_code
    mfg_record["daybookSetCode"] = daybook_set

    return post_mfg_customer(payload, domain, customer_code, token)


# =============================================================================
# SINGLE-ROW ENTRY POINT  (this replaces process_file()'s per-row body)
# =============================================================================

def load_row(record: dict, tm: TokenManager) -> tuple[bool, str]:
    """
    Process exactly one record. Returns (success, error_message).
    No file I/O — the caller (app/api/operations.py) owns persistence of
    the outcome, e.g. writing it back onto the batch's results.
    """
    data_operation = val(record, "Data Operation").upper() or "C"

    missing = check_mandatory(record, MANDATORY_COLUMNS)
    if missing:
        return False, f"Missing mandatory fields: {', '.join(missing)}"

    if data_operation not in {"C", "U"}:
        return False, "Data Operation must be C, U, or blank"

    is_create = data_operation == "C"

    if is_create:
        missing_domain = check_mandatory(record, MANDATORY_DOMAIN_COLUMNS)
        if missing_domain:
            return False, f"Missing domain setting fields: {', '.join(missing_domain)}"

    # ── Build payload ──────────────────────────────────────────────────
    if data_operation == "U":
        existing = get_customer(record.get("Shared Set", ""), record.get("Customer", ""), tm.get())
        if not existing.get("data") or not existing["data"].get("customerV2s"):
            return False, f"UPDATE failed: Customer '{record.get('Customer', '')}' not found in QAD"

        payload = existing["data"]
        customer = payload["customerV2s"][0]
        customer["businessRelationCode"] = val(record, "Business Relation")
        customer["isActive"] = val(record, "Active").lower() == "yes"
        customer["currencyCode"] = val(record, "Currency")
        customer["creditTermsCode"] = val(record, "Credit Terms")
        customer["creditRatingCode"] = val(record, "Credit Rating")
        customer["invoiceStatusCode"] = val(record, "Invoice Status")
        customer["taxZone"] = val(record, "Tax Zone")
        customer["telephone"] = val(record, "Telephone")
        customer["EMail"] = val(record, "Email")
        customer["invoiceControlGLProfileCode"] = val(record, "Invoice Control GL Profile")
        customer["creditNoteControlGLProfileCode"] = val(record, "Credit Note Control GL Profile")
        customer["prePaymentControlGLProfileCode"] = val(record, "Prepayment Control GL Profile")
        customer["salesAccountGLProfileCode"] = val(record, "Sales Account GL Profile")
    else:
        payload = build_payload(record)

    # ── Step 1: POST customer (one token-refresh retry) ─────────────────
    success, error_msg = False, ""
    for attempt in range(2):
        try:
            success, error_msg = post_customer(payload, tm.get(), is_create=is_create)
            break
        except TokenExpired:
            if attempt == 0:
                tm.refresh()
                continue
            error_msg = "Token refresh failed — unauthorised"
            break
        except requests.RequestException as e:
            error_msg = f"Network error: {e}"
            break

    if not success:
        return False, error_msg

    # ── Step 2 (CREATE only): domain settings ────────────────────────────
    if is_create:
        domain = val(record, "Domain")
        site_code = val(record, "Site Code")
        daybook_set = val(record, "Daybook Set")
        customer_code = val(record, "Customer")

        domain_ok, domain_err = False, ""
        for attempt in range(2):
            try:
                domain_ok, domain_err = update_domain_settings(
                    customer_code, domain, site_code, daybook_set, tm.get()
                )
                break
            except TokenExpired:
                if attempt == 0:
                    tm.refresh()
                    continue
                domain_err = "Token refresh failed — unauthorised"
                break
            except requests.RequestException as e:
                domain_err = f"Network error: {e}"
                break

        if not domain_ok:
            return False, f"Customer created but domain settings failed: {domain_err}"

    return True, ""
