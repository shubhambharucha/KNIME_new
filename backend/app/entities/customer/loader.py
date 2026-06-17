"""
app/entities/customer/loader.py
--------------------------------
Load Customer records into QAD customerV2s API.

Pipeline per record:
  1. Extract only customerCode + currencyCode from raw incoming JSON
  2. Derive businessRelationCode and businessRelationName from customerCode
  3. Merge with hardcoded DEFAULTS
  4. Validate mandatory fields
  5. Build { "customerV2s": [payload] }
  6. POST to QAD
  7. Return per-row result including the exact payload sent
"""

import logging
import requests

from app.config import CONFIG
from . import config

logger = logging.getLogger(__name__)

QAD_ENDPOINT = f"{CONFIG['qad']['base_url']}/api/erp/customerV2s"
QAD_VIEW_URI = "urn:be:com.qad.base.customer.ICustomerV2"


# ---------------------------------------------------------------------------
# Token management
# ---------------------------------------------------------------------------

class TokenManager:
    """Fetches and caches an OAuth token. Refreshes automatically on 401."""

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
        url = f"{CONFIG['qad']['base_url']}/oauth/token"
        resp = requests.post(url, data=CONFIG["qad"]["auth"], timeout=30)
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if not token:
            raise RuntimeError("OAuth response missing access_token")
        logger.info("Token obtained")
        return token


# ---------------------------------------------------------------------------
# Record construction
# ---------------------------------------------------------------------------

def _extract(raw: dict) -> dict:
    """
    Pull only customerCode and currencyCode out of the raw incoming record.
    Every other field is intentionally dropped here — they belong to a
    different environment and cause 500s if forwarded.
    """
    extracted = {}
    for src_key, dest_key in config.EXTRACT_FIELDS.items():
        value = raw.get(src_key)
        if value is not None and str(value).strip():
            extracted[dest_key] = value
    return extracted


def _build_record(extracted: dict) -> dict:
    """
    Given the two extracted fields, produce the complete record ready for
    the QAD payload by:
      1. Starting from a copy of DEFAULTS
      2. Overlaying the extracted fields (customerCode, currencyCode)
      3. Deriving businessRelationCode and businessRelationName from customerCode
      4. Deriving addressName and addressSearchName from customerCode
         (matches the pattern in the confirmed-working payload)
    """
    record = dict(config.DEFAULTS)

    # Overlay the two extracted fields
    record.update(extracted)

    customer_code = record.get("customerCode", "")

    # Derived fields — all tied to customerCode to mirror the working payload
    record["businessRelationCode"] = customer_code
    record["businessRelationName"] = customer_code
    record["addressName"] = customer_code
    record["addressSearchName"] = customer_code

    return record


def _validate(record: dict) -> tuple[bool, str]:
    """Check all mandatory fields are present and non-empty."""
    missing = [
        f for f in config.MANDATORY_FIELDS
        if not str(record.get(f, "")).strip()
    ]
    if missing:
        return False, f"Missing mandatory fields: {', '.join(missing)}"
    return True, ""


def _build_payload(record: dict) -> dict:
    """Wrap the record in the QAD-expected envelope, dropping any None/empty values."""
    clean = {k: v for k, v in record.items() if v is not None and str(v).strip() != ""}
    return {"customerV2s": [clean]}


# ---------------------------------------------------------------------------
# Batch loader
# ---------------------------------------------------------------------------

def load_batch(records: list[dict], token_manager: TokenManager) -> list[dict]:
    """
    Process and POST each record to QAD.

    Args:
        records:       Raw incoming records (full of fields we don't want).
        token_manager: OAuth token manager.

    Returns:
        List of per-row result dicts:
        {
            "row":          int,
            "customerCode": str,
            "ok":           bool,
            "error":        str | None,
            "payload_sent": dict,          # exact payload POSTed to QAD
            "status": {                    # populated on success
                "uri", "changeStatus", "isActive",
                "isBusinessRelationActive",
                "disallowedActions", "disallowedActionsMessage"
            } | None
        }
    """
    results = []
    token = token_manager.get()

    for row_idx, raw in enumerate(records):

        result = {
            "row": row_idx,
            "customerCode": raw.get("CustomerCode", raw.get("customerCode", "")),
            "ok": False,
            "error": None,
            "payload_sent": None,
            "status": None,
        }

        # --- Step 1: Extract only the two fields we need ---
        extracted = _extract(raw)

        if not extracted.get("customerCode"):
            result["error"] = "customerCode not found in incoming record"
            logger.warning(f"Row {row_idx}: {result['error']}")
            results.append(result)
            continue

        if not extracted.get("currencyCode"):
            result["error"] = "currencyCode not found in incoming record"
            logger.warning(f"Row {row_idx}: {result['error']}")
            results.append(result)
            continue

        # --- Step 2 & 3: Build full record from defaults + derived fields ---
        record = _build_record(extracted)

        # --- Step 4: Validate ---
        valid, error_msg = _validate(record)
        if not valid:
            result["error"] = error_msg
            logger.warning(f"Row {row_idx}: {error_msg}")
            results.append(result)
            continue

        # --- Step 5: Build payload ---
        payload = _build_payload(record)
        result["payload_sent"] = payload

        customer_code = record["customerCode"]
        shared_set_code = record["sharedSetCode"]

        query_params = {
            "sharedSetCode": shared_set_code,
            "customerCode": customer_code,
            "viewUri": QAD_VIEW_URI,
        }

        # --- Step 6: POST to QAD (retry once on 401) ---
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

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
                    resp_json = resp.json()
                    obj = resp_json.get("customerV2s", [{}])[0]
                    result["status"] = {
                        "uri":                       obj.get("uri"),
                        "changeStatus":              obj.get("changeStatus"),
                        "isActive":                  obj.get("isActive"),
                        "isBusinessRelationActive":  obj.get("isBusinessRelationActive"),
                        "disallowedActions":         obj.get("disallowedActions"),
                        "disallowedActionsMessage":  obj.get("disallowedActionsMessage"),
                    }
                    logger.info(
                        f"Row {row_idx} ✅ {customer_code} | "
                        f"changeStatus={result['status']['changeStatus']} "
                        f"isActive={result['status']['isActive']}"
                    )
                except Exception as parse_err:
                    logger.warning(f"Row {row_idx} ✅ {customer_code} — could not parse response: {parse_err}")
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