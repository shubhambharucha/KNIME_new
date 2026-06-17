"""
app/entities/customer/loader.py
--------------------------------
Load Customer records into QAD customerV2s API.

STRICT MODE: only customerCode and currencyCode come from the source
record. Everything else is hardcoded via config.DEFAULTS.

Flow:
  1. For each record (only customerCode + currencyCode survive aliasing)
  2. Derive businessRelationCode from customerCode
  3. Apply hardcoded defaults
  4. Validate mandatory fields
  5. Build customerV2s payload
  6. POST to QAD with query params
  7. Capture success (200) or error message
  8. Return per-row results
"""

import logging
import requests
from typing import Any

from app.config import CONFIG
from . import config

logger = logging.getLogger(__name__)

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


def _set_business_relation_code(record: dict) -> dict:
    """
    Every record creates a brand-new Business Relation
    (isCreateBusinessRelationRequired=True), so there's no existing
    BR code to look up. Use customerCode as the BR code.
    """
    if record.get("customerCode"):
        record["businessRelationCode"] = record["customerCode"]
    return record


def _apply_defaults(record: dict) -> dict:
    """
    Apply config.DEFAULTS to record. Since only customerCode and
    currencyCode come in, this effectively populates the entire rest
    of the payload.
    """
    for col, default_value in config.DEFAULTS.items():
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
    """
    customer_v2 = {}
    for key, value in record.items():
        if value is None or (isinstance(value, str) and not value.strip()):
            continue
        customer_v2[key] = value

    return {"customerV2s": [customer_v2]}


def _extract_status_fields(resp_json: dict) -> dict:
    """
    Pull out fields that tell us whether the created record is "live"
    (active, no pending change request, no blocked actions) vs sitting
    in a pending/draft state.
    """
    try:
        customer_obj = resp_json.get("customerV2s", [{}])[0]
    except (KeyError, IndexError, TypeError):
        customer_obj = {}

    return {
        "uri": customer_obj.get("uri"),
        "changeStatus": customer_obj.get("changeStatus"),
        "isActive": customer_obj.get("isActive"),
        "isBusinessRelationActive": customer_obj.get("isBusinessRelationActive"),
        "disallowedActions": customer_obj.get("disallowedActions"),
        "disallowedActionsMessage": customer_obj.get("disallowedActionsMessage"),
    }


def load_batch(records: list[dict], token_manager: TokenManager) -> list[dict]:
    """
    Load all records in the batch into QAD.

    Args:
        records: List of flattened, aliased customer records
                 (only customerCode + currencyCode populated from source)
        token_manager: TokenManager instance for OAuth

    Returns:
        List of per-row results:
        [
            {
                "row": 0,
                "ok": True,
                "customerCode": "EXP004",
                "error": None,
                "status": { "uri": ..., "changeStatus": ..., "isActive": ..., ... }
            },
            ...
        ]
    """
    results = []
    token = token_manager.get()

    for row_idx, record in enumerate(records):
        # Only customerCode and currencyCode should exist on `record`
        # at this point (everything else stripped by COLUMN_ALIASES).
        record = dict(record)

        result = {
            "row": row_idx,
            "ok": False,
            "customerCode": record.get("customerCode", ""),
            "error": None,
            "status": None,
        }

        try:
            record = _set_business_relation_code(record)
            record = _apply_defaults(record)

            is_valid, error_msg = _validate_mandatory_fields(record)
            if not is_valid:
                result["error"] = error_msg
                results.append(result)
                logger.warning(f"Row {row_idx}: {error_msg}")
                continue

            payload = _build_customer_payload(record)

        except Exception as e:
            result["error"] = f"Payload build failed: {str(e)}"
            results.append(result)
            logger.error(f"Row {row_idx}: {result['error']}")
            continue

        customer_code = record.get("customerCode", "")
        shared_set_code = record.get("sharedSetCode", "")

        if not customer_code or not shared_set_code:
            result["error"] = "customerCode and sharedSetCode required for query params"
            results.append(result)
            logger.warning(f"Row {row_idx}: {result['error']}")
            continue

        query_params = {
            "sharedSetCode": shared_set_code,
            "customerCode": customer_code,
            "viewUri": QAD_VIEW_URI,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

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

                    try:
                        resp_json = resp.json()
                        status_fields = _extract_status_fields(resp_json)
                        result["status"] = status_fields
                        logger.info(
                            f"Row {row_idx}: ✅ {customer_code} | "
                            f"changeStatus={status_fields['changeStatus']} "
                            f"isActive={status_fields['isActive']} "
                            f"isBusinessRelationActive={status_fields['isBusinessRelationActive']} "
                            f"disallowedActions={status_fields['disallowedActions']!r}"
                        )
                    except Exception as parse_err:
                        logger.warning(
                            f"Row {row_idx}: ✅ {customer_code} but could not parse "
                            f"response body for status fields: {parse_err}"
                        )

                    retry = False

                elif resp.status_code == 401:
                    logger.warning(f"Row {row_idx}: Token expired, refreshing...")
                    token = token_manager.refresh()
                    headers["Authorization"] = f"Bearer {token}"

                else:
                    error_text = resp.text[:500]
                    result["error"] = f"HTTP {resp.status_code}: {error_text}"
                    logger.error(f"Row {row_idx}: {result['error']}")
                    retry = False

            except requests.RequestException as e:
                result["error"] = f"Request failed: {str(e)}"
                logger.error(f"Row {row_idx}: {result['error']}")
                retry = False

        results.append(result)

    return results