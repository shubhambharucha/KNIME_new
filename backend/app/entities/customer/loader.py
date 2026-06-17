"""
app/entities/customer/loader.py
--------------------------------
Load Customer records into QAD customerV2s API.

Flow:
  1. For each flattened record from the batch
  2. Validate mandatory fields
  3. Build customerV2s payload
  4. POST to QAD with query params (sharedSetCode, customerCode, viewUri)
  5. Capture success (200) or error message
  6. Return per-row results
"""

import logging
import requests
from typing import Any

from app.config import CONFIG
from . import config as customer_config

logger = logging.getLogger(__name__)

# QAD customerV2s API base endpoint
QAD_CUSTOMER_ENDPOINT = f"{CONFIG['qad']['base_url']}/api/erp/customerV2s"
QAD_VIEW_URI = "urn:be:com.qad.base.customer.ICustomerV2"


class TokenManager:
    """Manages OAuth token for the customer loader. Refreshes on 401."""

    def __init__(self):
        self._token: str | None = None

    def get(self) -> str:
        if self._token is None:
            self._token = self._fetch_token()
        return self._token

    def refresh(self) -> str:
        self._token = self._fetch_token()
        return self._token

    def _fetch_token(self) -> str:
        url = f"{CONFIG['qad']['base_url']}/oauth/token"
        resp = requests.post(url, data=CONFIG["qad"]["auth"], timeout=30)
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if not token:
            raise RuntimeError("OAuth response did not contain access_token")
        logger.info("✅ New token obtained")
        return token


def _validate_mandatory_fields(record: dict) -> tuple[bool, str]:
    """
    Check that all mandatory fields are present and non-empty.
    Returns (is_valid, error_message)
    """
    missing = []
    for col in customer_config.MANDATORY_COLUMNS:
        value = record.get(col)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(col)

    if missing:
        return False, f"Missing mandatory fields: {', '.join(missing)}"
    return True, ""


def _build_customer_payload(record: dict) -> dict:
    """
    Build the customerV2s payload (wrapped in { "customerV2s": [...] }).
    Takes the flattened, aliased record and constructs the API request body.
    """
    # Copy customerCode → businessRelationCode if not explicitly provided
    if not record.get("businessRelationCode") and record.get("customerCode"):
        record["businessRelationCode"] = record["customerCode"]

    # Populate addressName and addressSearchName from businessRelationName if not set
    if not record.get("addressName"):
        record["addressName"] = record.get("businessRelationName", "")
    if not record.get("addressSearchName"):
        record["addressSearchName"] = record.get("businessRelationName", "")

    customer_v2 = {}
    for key, value in record.items():
        # Skip None and empty string values (QAD handles them as omitted)
        if value is None or (isinstance(value, str) and not value.strip()):
            continue
        customer_v2[key] = value

    return {"customerV2s": [customer_v2]}


def load_batch(records: list[dict], token_manager: TokenManager) -> list[dict]:
    """
    Load all records in the batch into QAD.

    Args:
        records: List of flattened, aliased customer records
        token_manager: TokenManager instance for OAuth

    Returns:
        List of per-row results:
        [
            {
                "row": 0,
                "ok": True,
                "customerCode": "CUST001",
                "error": None
            },
            {
                "row": 1,
                "ok": False,
                "customerCode": "CUST002",
                "error": "Missing mandatory fields: creditTermsCode"
            },
            ...
        ]
    """
    results = []
    token = token_manager.get()

    for row_idx, record in enumerate(records):
        result = {
            "row": row_idx,
            "ok": False,
            "customerCode": record.get("customerCode", ""),
            "error": None,
        }

        # Step 1: Validate mandatory fields
        is_valid, error_msg = _validate_mandatory_fields(record)
        if not is_valid:
            result["error"] = error_msg
            results.append(result)
            logger.warning(f"Row {row_idx}: {error_msg}")
            continue

        # Step 2: Build payload
        try:
            payload = _build_customer_payload(record)
        except Exception as e:
            result["error"] = f"Payload build failed: {str(e)}"
            results.append(result)
            logger.error(f"Row {row_idx}: {result['error']}")
            continue

        # Step 3: Extract query params
        customer_code = record.get("customerCode", "")
        shared_set_code = record.get("sharedSetCode", "")

        if not customer_code or not shared_set_code:
            result["error"] = "customerCode and sharedSetCode required for query params"
            results.append(result)
            logger.warning(f"Row {row_idx}: {result['error']}")
            continue

        # Step 4: Prepare request
        query_params = {
            "sharedSetCode": shared_set_code,
            "customerCode": customer_code,
            "viewUri": QAD_VIEW_URI,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        # Step 5: POST with retry on 401 (token refresh)
        retry = True
        while retry:
            try:
                resp = requests.post(
                    QAD_CUSTOMER_ENDPOINT,
                    params=query_params,
                    json=payload,
                    headers=headers,
                    timeout=30,
                )

                if resp.status_code == 200:
                    result["ok"] = True
                    result["error"] = None
                    logger.info(f"Row {row_idx}: ✅ {customer_code}")
                    retry = False

                elif resp.status_code == 401:
                    # Token expired, refresh and retry
                    logger.warning(f"Row {row_idx}: Token expired, refreshing...")
                    token = token_manager.refresh()
                    headers["Authorization"] = f"Bearer {token}"
                    # Loop will retry with new token

                else:
                    # Other error (4xx, 5xx)
                    error_text = resp.text[:500]  # Truncate long error messages
                    result["error"] = f"HTTP {resp.status_code}: {error_text}"
                    logger.error(f"Row {row_idx}: {result['error']}")
                    retry = False

            except requests.RequestException as e:
                result["error"] = f"Request failed: {str(e)}"
                logger.error(f"Row {row_idx}: {result['error']}")
                retry = False

        results.append(result)

    return results