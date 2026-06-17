"""
app/entities/customer/loader.py
"""

import logging
import requests

from app.config import CONFIG

logger = logging.getLogger(__name__)

QAD_ENDPOINT = f"{CONFIG['qad']['base_url']}/api/erp/customerV2s"
QAD_VIEW_URI = "urn:be:com.qad.base.customer.ICustomerV2"


class TokenManager:
    def __init__(self):
        self._token: str | None = None

    def get(self) -> str:
        if self._token is None:
            self._token = self._fetch()
        return self._token

    def refresh(self) -> str:
        self._token = self._fetch()
        return self._token

    def _fetch(self) -> str:
        resp = requests.post(
            f"{CONFIG['qad']['base_url']}/oauth/token",
            data=CONFIG["qad"]["auth"],
            timeout=30,
        )
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if not token:
            raise RuntimeError("OAuth response missing access_token")
        logger.info("Token obtained")
        return token


def val(row: dict, col: str) -> str:
    """Safely extract and trim a value from row by column name."""
    v = row.get(col)
    return str(v).strip() if v is not None else ""


def build_payload(row: dict) -> dict:
    """
    Build a complete, valid QAD customerV2 payload from an Excel row.
    Constructs URI, maps all fields, applies defaults.
    """
    customer_code = val(row, "Customer")
    shared_set    = "QMI-CUST"
    uri           = f"urn:be:com.qad.base.customer.ICustomerV2:{shared_set}.{customer_code}"

    # Helper to convert "yes"/"no" to boolean
    def to_bool(s: str, default: bool = False) -> bool:
        return s.lower() in ("yes", "true", "1") if s else default

    # Helper to safely convert to float
    def to_float(s: str, default: float = 0.0) -> float:
        try:
            return float(s) if s else default
        except (ValueError, TypeError):
            return default

    return {
        "supplementaryMessages": [],
        "customerV2s": [
            {
                # ── URIs / Identity ───────────────────────────────────────────
                "uri":                                      uri,
                "instanceURI":                              uri,
                "customerCode":                             customer_code,
                "customerID":                               0,
                "sharedSetCode":                            shared_set,
                "sharedSetID":                              0,

                # ── Business Relation ─────────────────────────────────────────
                "businessRelationCode":                     val(row, "Business Relation"),
                "businessRelationID":                       0,
                "businessRelationName":                     "",
                "businessRelationName2":                    "",
                "businessRelationName3":                    "",
                "businessRelationConcurrencyHash":          "",
                "isBusinessRelationActive":                 True,
                "isBusinessRelationFieldsEnabled":          True,
                "isBusinessRelationIntercompany":           False,
                "isCreateBusinessRelationRequired":         True,
                "isInternalEntity":                         False,
                "intercompanyCode":                         "",

                # ── Address ───────────────────────────────────────────────────
                "addressID":                                0,
                "addressName":                              val(row, "Name"),
                "addressSearchName":                        val(row, "Search Name"),
                "addressTypeCode":                          val(row, "Address Type"),
                "addressConcurrencyHash":                   "",
                "street1":                                  val(row, "Address 1"),
                "street2":                                  val(row, "Address 2"),
                "street3":                                  "",
                "city":                                     val(row, "City"),
                "cityCode":                                 "",
                "zipCode":                                  val(row, "Postal Code"),
                "stateCode":                                val(row, "State"),
                "stateDescription":                         "",
                "stateTax":                                 "",
                "countryCode":                              val(row, "Country"),
                "countryDescription":                       "",
                "countyCode":                               "",
                "countyDescription":                        "",
                "postalFormat":                             "0",
                "latitude":                                 0,
                "longitude":                                0,
                "isTemporaryAddress":                       False,

                # ── Status / Concurrency ──────────────────────────────────────
                "changeStatus":                             "2",
                "dataOperation":                            "",
                "concurrencyHash":                          "",
                "disallowedActions":                        "",
                "disallowedActionsMessage":                 "",
                "isPredefaulted":                           False,
                "isDomainRestricted":                       False,
                "lastModifiedDate":                         "",
                "lastModifiedTime":                         0,
                "lastModifiedUser":                         "",

                # ── Active / Type ─────────────────────────────────────────────
                "isActive":                                 to_bool(val(row, "Active")),
                "customerTypeCode":                         val(row, "Customer Type"),
                "customerTypeID":                           0,

                # ── Currency / Language ───────────────────────────────────────
                "currencyCode":                             val(row, "Currency"),
                "currencyDescription":                      "",
                "currencyID":                               0,
                "customerCurrencyCode":                     val(row, "Currency"),
                "languageCode":                             val(row, "Language"),
                "languageDescription":                      "",

                # ── Credit Terms ──────────────────────────────────────────────
                "creditTermsCode":                          val(row, "Credit Terms"),
                "creditTermsDescription":                   "",
                "creditTermsID":                            0,
                "creditTermsType":                          "",

                # ── Invoice / Status ──────────────────────────────────────────
                "invoiceStatusCode":                        val(row, "Invoice Status"),
                "invoiceStatusDescription":                 "",
                "invoiceStatusID":                          0,
                "isInvoiceByAuthorization":                 False,
                "isWithPreInvoiceGroup":                    False,
                "isPrintBillWithItemDetails":               False,

                # ── GL Profiles ───────────────────────────────────────────────
                "invoiceControlGLProfileCode":              val(row, "Invoice Control GL Profile"),
                "invoiceControlGLProfileDesc":              "",
                "invoiceControlGLProfileID":                0,
                "creditNoteControlGLProfileCode":           val(row, "Credit Note Control GL Profile"),
                "creditNoteControlGLProfileDesc":           "",
                "creditNoteControlGLProfileID":             0,
                "prePaymentControlGLProfileCode":           val(row, "Prepayment Control GL Profile"),
                "prePaymentControlGLProfileDesc":           "",
                "prePaymentControlGLProfileID":             0,
                "salesAccountGLProfileCode":                val(row, "Sales Account GL Profile"),
                "salesAccountGLProfileDesc":                "",
                "salesAccountGLProfileID":                  0,
                "deductionControlGLProfileCode":            "",
                "deductionControlGLProfileDesc":            "",
                "deductionControlGLProfileID":              0,
                "financeChargeGLProfileCode":               "",
                "financeChargeGLProfileDesc":               "",
                "financeChargeGLProfileID":                 0,

                # ── Revenue Recognition GL Profiles ───────────────────────────
                "accruedRevRecGLProfileCode":               "",
                "accruedRevRecGLProfileDesc":               "",
                "accruedRevRecGLProfileID":                 0,
                "deferredRevRecGLProfileCode":              "",
                "deferredRevRecGLProfileDesc":              "",
                "deferredRevRecGLProfileID":                0,
                "COGSAccruedRevRecGLProfileCode":           "",
                "COGSAccruedRevRecGLProfileDesc":           "",
                "COGSAccruedRevRecGLProfileID":             0,
                "COGSDeferredRevRecGLProfileCode":          "",
                "COGSDeferredRevRecGLProfileDesc":          "",
                "COGSDeferredRevRecGLProfileID":            0,
                "COGSOffsetRevRecGLProfileCode":            "",
                "COGSOffsetRevRecGLProfileDesc":            "",
                "COGSOffsetRevRecGLProfileID":              0,
                "isAutoCreateRevRecContracts":              False,
                "revRecRuleID":                             0,
                "reviewRequiredForContracts":               "",

                # ── Tax ───────────────────────────────────────────────────────
                "taxZone":                                  val(row, "Tax Zone"),
                "taxZoneDescription":                       "",
                "taxClass":                                 "",
                "taxClassDescription":                      "",
                "taxDeclaration":                           0,
                "taxUsage":                                 "",
                "taxUsageDescription":                      "",
                "isTaxable":                                True,
                "isTaxInCity":                              True,
                "isTaxIncluded":                            False,
                "isTaxReport":                              False,
                "isLastFiling":                             False,
                "isReportedIN":                             False,
                "isElectronicInvoiceIN":                    False,
                "federalTax":                               "",
                "miscellaneousTax1":                        "",
                "miscellaneousTax2":                        "",
                "miscellaneousTax3":                        "",
                "customerGTVatTransType":                   "",
                "vatDeliveryType":                          "",
                "vatPercentageLevel":                       "",
                "nameControl":                              "",
                "EORINumber":                               "",

                # ── Credit Limit ──────────────────────────────────────────────
                "fixedCreditLimit":                         to_float(val(row, "Fixed Credit Limit")),
                "highCredit":                               0,
                "isFixedCreditLimit":                       True,
                "isLockedCreditLimit":                      to_bool(val(row, "Credit Hold")),
                "isToBeLockedCreditLimit":                  False,
                "isOverruleAllowedSOCreditLimit":           True,
                "isCheckBeforeSOCreditLimit":               False,
                "isCheckAfterSOCreditLimit":                False,
                "isCheckBeforeInvoiceCreditLimit":          False,
                "isCheckAfterInvoiceCreditLimit":           False,
                "isOverAllowedInvoiceCreditLimit":          False,
                "isIncludeDraftCreditLimit":                False,
                "isIncludeOpenItemsCreditLimit":            True,
                "isIncludeSOCheckCreditLimit":              False,
                "isMaxDaysOverdueCreditLimit":              False,
                "isTurnOverCreditLimit":                    False,
                "maxDaysCreditLimit":                       0,
                "overToleranceAmount":                      0,
                "overTolerancePercent":                     0,
                "shortToleranceAmount":                     0,
                "shortTolerancePercent":                    0,
                "warningCreditLimitPercent":                0,
                "turnoverCreditLimitPercent":               0,
                "totalDaysLate":                            0,
                "totalNumberOfInvoices":                    0,
                "creditRatingCode":                         val(row, "Credit Rating"),
                "creditRatingID":                           0,
                "creditAgencyReference":                    "",

                # ── Finance Charges / Reminders / Statements ──────────────────
                "isFinanceCharge":                          False,
                "isPrintReminder":                          False,
                "isReminderRequired":                       False,
                "isPrintStatement":                         False,
                "reminderCountReset":                       False,
                "reminderAddressChangeStatus":              "",
                "reminderAddressID":                        0,
                "reminderAddressTypeCode":                  "",
                "reminderCustContactV2s":                   [],

                # ── Payment ───────────────────────────────────────────────────
                "paymentGroupCode":                         "",
                "paymentGroupDescription":                  "",
                "paymentGroupID":                           0,
                "domiciliationNumber":                      0,
                "isToleranceFromOwnBank":                   False,
                "isCompensationAllowed":                    False,

                # ── Billing ───────────────────────────────────────────────────
                "billToCustomerCode":                       "",
                "billToCustomerID":                         0,
                "billCollectorCode":                        "",
                "billCollectorID":                          0,
                "billingScheduleCode":                      "",
                "billingScheduleDescription":               "",
                "billingScheduleID":                        0,
                "statementCycle":                           "",
                "subAccountProfileCode":                    "",
                "subAccountProfileDesc":                    "",
                "subAccountProfileID":                      0,

                # ── Corporate Group ───────────────────────────────────────────
                "corporateGroupCode":                       "",
                "corporateGroupDescription":                "",
                "corporateGroupID":                         0,

                # ── Contact ───────────────────────────────────────────────────
                "EMail":                                    val(row, "Email"),
                "fax":                                      "",
                "telephone":                                val(row, "Telephone"),
                "webSite":                                  "",
                "commentNote":                              "",

                # ── Deduction ─────────────────────────────────────────────────
                "customerIsInclDeduction":                  False,

                # ── Custom Fields ─────────────────────────────────────────────
                "customShort0":  "", "customShort1":  "", "customShort2":  "",
                "customShort3":  "", "customShort4":  "", "customShort5":  "",
                "customShort6":  "", "customShort7":  "", "customShort8":  "",
                "customShort9":  "", "customShort10": "", "customShort11": "",
                "customShort12": "", "customShort13": "", "customShort14": "",
                "customShort15": "", "customShort16": "", "customShort17": "",
                "customShort18": "", "customShort19": "",
                "customLong0":   "", "customLong1":   "",
                "customNote":    "",
                "customCombo0":  "", "customCombo1":  "", "customCombo2":  "",
                "customCombo3":  "", "customCombo4":  "", "customCombo5":  "",
                "customCombo6":  "", "customCombo7":  "", "customCombo8":  "",
                "customCombo9":  "", "customCombo10": "", "customCombo11": "",
                "customCombo12": "", "customCombo13": "", "customCombo14": "",
                "customDecimal0": 0, "customDecimal1": 0, "customDecimal2": 0,
                "customDecimal3": 0, "customDecimal4": 0,
                "customInteger0": 0, "customInteger1": 0, "customInteger2": 0,
                "customInteger3": 0, "customInteger4": 0,

                # ── Sub-lists ─────────────────────────────────────────────────
                "customerContactV2s":                       [],
                "customerSafDefaultV2s":                    [],
                "bankNumberRefV2s":                         [],
                "MDMBankNrSharedSets":                      [],
            }
        ],
    }


def load_batch(records: list[dict], token_manager: TokenManager) -> list[dict]:
    """
    Load a batch of customer records to QAD.
    Each record is a dict of Excel column values.
    Returns list of result dicts with status for each row.
    """
    results = []
    token = token_manager.get()

    for row_idx, raw in enumerate(records):

        customer_code = val(raw, "Customer")
        result = {
            "row":          row_idx,
            "customerCode": customer_code,
            "ok":           False,
            "error":        None,
            "payload_sent": None,
            "status":       None,
        }

        # --- 1. Build complete payload ---
        try:
            payload = build_payload(raw)
        except Exception as e:
            result["error"] = f"Payload construction failed: {e}"
            logger.error(f"Row {row_idx}: {result['error']}")
            results.append(result)
            continue

        # --- 2. Validate mandatory fields exist in payload ---
        mandatory = [
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
        customer_obj = payload["customerV2s"][0]
        missing = [f for f in mandatory if not str(customer_obj.get(f, "")).strip()]
        if missing:
            result["error"] = f"Missing mandatory fields: {', '.join(missing)}"
            logger.warning(f"Row {row_idx}: {result['error']}")
            results.append(result)
            continue

        result["payload_sent"] = payload

        # --- 3. Prepare request ---
        shared_set = val(raw, "Shared Set")
        query_params = {
            "sharedSetCode": shared_set,
            "customerCode":  customer_code,
            "viewUri":       QAD_VIEW_URI,
        }
        headers = {
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {token}",
        }

        # --- 4. POST with retry on 401 ---
        for attempt in range(2):
            try:
                resp = requests.post(
                    QAD_ENDPOINT,
                    params=query_params,
                    json=payload,
                    headers=headers,
                    timeout=30,
                )
            except requests.RequestException as e:
                result["error"] = f"Request failed: {e}"
                logger.error(f"Row {row_idx} ({customer_code}): {result['error']}")
                break

            if resp.status_code in (200, 201):
                result["ok"] = True
                try:
                    obj = resp.json().get("customerV2s", [{}])[0]
                    result["status"] = {
                        "uri":                      obj.get("uri"),
                        "changeStatus":             obj.get("changeStatus"),
                        "isActive":                 obj.get("isActive"),
                        "isBusinessRelationActive": obj.get("isBusinessRelationActive"),
                        "disallowedActions":        obj.get("disallowedActions"),
                        "disallowedActionsMessage": obj.get("disallowedActionsMessage"),
                    }
                    logger.info(
                        f"Row {row_idx} ✅ {customer_code} | "
                        f"changeStatus={result['status']['changeStatus']} "
                        f"isActive={result['status']['isActive']}"
                    )
                except Exception as e:
                    logger.warning(f"Row {row_idx} ✅ {customer_code} — could not parse response: {e}")
                break

            elif resp.status_code == 401 and attempt == 0:
                logger.warning(f"Row {row_idx}: 401 — refreshing token and retrying")
                token = token_manager.refresh()
                headers["Authorization"] = f"Bearer {token}"

            else:
                result["error"] = f"HTTP {resp.status_code}: {resp.text[:500]}"
                logger.error(f"Row {row_idx} ({customer_code}): {result['error']}")
                break

        results.append(result)

    return results