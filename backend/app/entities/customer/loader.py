"""
app/entities/customer/loader.py

Customer Loader
---------------
Responsibilities:
    - OAuth token management
    - Build minimal QAD customer payload
    - POST customer payload to AUX
    - Retry once on 401
    - Return structured results
"""

import logging
import requests

logger = logging.getLogger(__name__)

# =============================================================================
# AUTH / ENDPOINTS
# =============================================================================

TOKEN_URL = "https://cat5-devl.adaptive.qad.com/clouderp/oauth/token"

UPLOAD_URL = (
    "https://cat5-devl.adaptive.qad.com/clouderp/api/erp/customerV2s"
    "?viewUri=urn:be:com.qad.base.customer.ICustomerV2"
)

VIEW_URI = "urn:be:com.qad.base.customer.ICustomerV2"

SHARED_SET = "QMI-CUST"

AUTH_PARAMS = {
    "client_id": "afb97fd221925b87f01489aeb0e02e81",
    "username": "demo",
    "password": "qad",
    "grant_type": "password",
}


# =============================================================================
# TOKEN MANAGEMENT
# =============================================================================

class TokenManager:
    def __init__(self):
        self._token = None

    def get(self):
        if not self._token:
            self._token = self._fetch()
        return self._token

    def refresh(self):
        self._token = self._fetch()
        return self._token

    def _fetch(self):
        logger.info("Requesting OAuth token...")

        resp = requests.post(
            TOKEN_URL,
            params=AUTH_PARAMS,
            timeout=30,
        )

        resp.raise_for_status()

        token = resp.json().get("access_token")

        if not token:
            raise RuntimeError("OAuth response missing access_token")

        logger.info("OAuth token acquired")
        return token


# =============================================================================
# EXCEPTIONS
# =============================================================================

class _TokenExpired(Exception):
    pass


# =============================================================================
# PAYLOAD BUILDER
# =============================================================================

def build_payload(row: dict) -> dict:
    """
    Build minimal customer payload.

    Incoming flattened record:
    {
        "customerCode": "...",
        "businessRelationCode": "...",
        ...
    }

    We only inject:
        - sharedSetCode
        - uri
        - instanceURI
    """

    customer_code = str(
        row.get("customerCode")
        or row.get("Customer")
        or ""
    ).strip()

    record = {}

    # Keep all non-empty incoming values
    for key, value in row.items():
        if value is None:
            continue

        if isinstance(value, str) and not value.strip():
            continue

        record[key] = value

    # Force shared set
    record["sharedSetCode"] = SHARED_SET

    # Build URI
    uri = (
        f"{VIEW_URI}:"
        f"{SHARED_SET}.{customer_code}"
    )

    record["uri"] = uri
    record["instanceURI"] = uri

    return {
        "supplementaryMessages": [],
        "customerV2s": [record],
    }


# =============================================================================
# VALIDATION
# =============================================================================

def validate(row: dict) -> list[str]:
    missing = []

    customer_code = (
        row.get("customerCode")
        or row.get("Customer")
    )

    if not str(customer_code or "").strip():
        missing.append("customerCode")

    return missing


# =============================================================================
# POST CUSTOMER
# =============================================================================

def post_customer(payload: dict, token: str):
    """
    POST payload to Customer AUX endpoint.

    Returns:
        (success, response_data)

    Raises:
        _TokenExpired on 401
    """

    resp = requests.post(
        UPLOAD_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )

    if resp.status_code == 401:
        raise _TokenExpired()

    try:
        resp_json = resp.json()
    except Exception:
        resp_json = {}

    # -------------------------------------------------------------------------
    # SUCCESS CASE 1 - submitResult.success
    # -------------------------------------------------------------------------
    submit = resp_json.get("submitResult", {})

    if submit.get("success") is True:
        return True, {
            "status_code": resp.status_code,
            "response": resp_json,
        }

    # -------------------------------------------------------------------------
    # SUCCESS CASE 2 - HTTP 200/201 returned customer object
    # -------------------------------------------------------------------------
    if resp.status_code in (200, 201):

        if resp_json.get("customerV2s"):
            return True, {
                "status_code": resp.status_code,
                "response": resp_json,
            }

    # -------------------------------------------------------------------------
    # ERROR HANDLING
    # -------------------------------------------------------------------------
    error_messages = []
    bad_fields = []

    for err in submit.get("errors", []):

        field_name = (
            err.get("fieldName")
            or err.get("field")
            or err.get("name")
            or ""
        ).strip()

        message = err.get("message", "").strip()

        if field_name:
            bad_fields.append(field_name)

        if message:
            error_messages.append(message)

    error_text = (
        "; ".join(error_messages)
        or resp_json.get("message")
        or resp.text[:500]
        or f"HTTP {resp.status_code}"
    )

    return False, {
        "status_code": resp.status_code,
        "error": error_text,
        "fields": bad_fields,
        "response": resp_json,
    }


# =============================================================================
# LOAD BATCH
# =============================================================================

def load_batch(records: list[dict], token_manager: TokenManager):
    """
    Entry point used by /api/load
    """

    results = []

    token = token_manager.get()

    for row_idx, row in enumerate(records):

        customer_code = (
            row.get("customerCode")
            or row.get("Customer")
            or ""
        )

        result = {
            "row": row_idx,
            "customerCode": customer_code,
            "ok": False,
            "error": None,
            "payload_sent": None,
            "response": None,
        }

        # ---------------------------------------------------------------------
        # VALIDATION
        # ---------------------------------------------------------------------
        missing = validate(row)

        if missing:
            result["error"] = (
                f"Missing required fields: {', '.join(missing)}"
            )

            results.append(result)
            continue

        # ---------------------------------------------------------------------
        # BUILD PAYLOAD
        # ---------------------------------------------------------------------
        payload = build_payload(row)

        result["payload_sent"] = payload

        # ---------------------------------------------------------------------
        # POST (retry once on 401)
        # ---------------------------------------------------------------------
        for attempt in range(2):

            try:
                success, response_data = post_customer(
                    payload,
                    token
                )

                if success:
                    result["ok"] = True
                    result["response"] = response_data

                    logger.info(
                        f"Customer loaded successfully: {customer_code}"
                    )

                else:
                    result["error"] = response_data.get("error")
                    result["response"] = response_data

                    logger.error(
                        f"Customer load failed: "
                        f"{customer_code} - {result['error']}"
                    )

                break

            except _TokenExpired:

                if attempt == 0:
                    logger.warning(
                        "401 received. Refreshing token and retrying..."
                    )

                    token = token_manager.refresh()
                    continue

                result["error"] = "Token refresh failed"
                break

            except requests.exceptions.Timeout:

                result["error"] = "Request timed out after 30 seconds"

                logger.error(
                    f"Timeout posting customer {customer_code}"
                )

                break

            except Exception as exc:

                result["error"] = str(exc)

                logger.exception(
                    f"Unexpected loader error for {customer_code}"
                )

                break

        results.append(result)

    return results