"""
app/entities/customer/loader.py
--------------------------------
Load Customer records into QAD customerV2s API.

Handles:
- Integer GL profile IDs → string conversions
- Empty mandatory fields → apply defaults
- Address population from businessRelationName
- Per-row success/error tracking

Flow:
  1. For each flattened record from the batch
  2. Apply type coercions (IDs → strings)
  3. Validate mandatory fields
  4. Build customerV2s payload
  5. POST to QAD with query params
  6. Capture success (200) or error message
  7. Return per-row results
"""

import logging
import requests
from typing import Any

from app.config import CONFIG
from . import config

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


def _coerce_types(record: dict) -> dict:
    """
    Convert integer GL profile IDs to strings.
    Ensure all GL codes are strings for API compatibility.
    """
    gl_profile_fields = [
        "invoiceControlGLProfileCode",
        "creditNoteControlGLProfileCode",
        "prePaymentControlGLProfileCode",
        "salesAccountGLProfileCode",
    ]
    
    for field in gl_profile_fields:
        value = record.get(field)
        if value is not None:
            if isinstance(value, int):
                # Convert integer ID to string
                record[field] = str(value)
            elif isinstance(value, str) and value.strip():
                # Keep non-empty strings as-is
                pass
            else:
                # Remove empty/None values; will be filled by defaults
                if field in record:
                    del record[field]
    
    return record


def _apply_defaults(record: dict) -> dict:
    """
    Apply DEFAULTS to record where fields are empty/missing.
    """
    for col, default_value in config.DEFAULTS.items():
        # Only apply if field is missing or empty
        if col not in record or record[col] is None or (isinstance(record[col], str) and not record[col].strip()):
            record[col] = default_value
    
    return record


def _validate_mandatory_fields(record: dict) -> tuple[bool, str]:
    """
    Check that all mandatory fields are present and non-empty.
    Returns (is_valid, error_message)
    """
    missing = []
    for col in config.MANDATORY_COLUMNS:
        value = record.get(col)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(col)

    if missing:
        return False, f"Missing mandatory: {', '.join(missing)}"
    return True, ""


def _build_customer_payload(record: dict) -> dict:
    """
    Build the customerV2s payload (wrapped in { "customerV2s": [...] }).
    
    Populates:
    - addressName and addressSearchName from businessRelationName if not set
    - Removes None/empty values to keep payload clean
    """
    # Populate address fields from businessRelationName
    if not record.get("addressName") and record.get("businessRelationName"):
        record["addressName"] = record["businessRelationName"]
    if not record.get("addressSearchName") and record.get("businessRelationName"):
        record["addressSearchName"] = record["businessRelationName"]

    # Build clean payload (exclude None and empty strings)
    customer_v2 = {}
    for key, value in record.items():
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
                "customerCode": "EXP004",
                "error": None
            },
            {
                "row": 1,
                "ok": False,
                "customerCode": "EXP009",
                "error": "Missing mandatory: invoiceControlGLProfileCode"
            },
            ...
        ]
    """
    results = []
    token = token_manager.get()

    for row_idx, record in enumerate(records):
        # Make a copy to avoid mutating original
        record = dict(record)
        
        result = {
            "row": row_idx,
            "ok": False,
            "customerCode": record.get("customerCode", ""),
            "error": None,
        }

        try:
            # Step 1: Type coercions (IDs → strings)
            record = _coerce_types(record)

            # Step 2: Apply defaults
            record = _apply_defaults(record)

            # Step 3: Validate mandatory fields
            is_valid, error_msg = _validate_mandatory_fields(record)
            if not is_valid:
                result["error"] = error_msg
                results.append(result)
                logger.warning(f"Row {row_idx}: {error_msg}")
                continue

            # Step 4: Build payload
            payload = _build_customer_payload(record)

        except Exception as e:
            result["error"] = f"Payload build failed: {str(e)}"
            results.append(result)
            logger.error(f"Row {row_idx}: {result['error']}")
            continue

        # Step 5: Extract query params
        customer_code = record.get("customerCode", "")
        shared_set_code = record.get("sharedSetCode", "")

        if not customer_code or not shared_set_code:
            result["error"] = "customerCode and sharedSetCode required for query params"
            results.append(result)
            logger.warning(f"Row {row_idx}: {result['error']}")
            continue

        # Step 6: Prepare request
        query_params = {
            "sharedSetCode": shared_set_code,
            "customerCode": customer_code,
            "viewUri": QAD_VIEW_URI,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        # Step 7: POST with retry on 401 (token refresh)
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

                if resp.status_code in (200, 201):
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