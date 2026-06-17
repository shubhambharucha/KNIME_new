"""
app/entities/customer/loader.py
"""

import logging
import requests

from app.config import CONFIG
from . import config

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


def load_batch(records: list[dict], token_manager: TokenManager) -> list[dict]:
    results = []
    token = token_manager.get()

    for row_idx, raw in enumerate(records):

        result = {
            "row":          row_idx,
            "customerCode": raw.get("customerCode", ""),
            "ok":           False,
            "error":        None,
            "payload_sent": None,
            "status":       None,
        }

        # --- 1. Seed record from HARDCODED (full payload template with defaults) ---
        #record = dict(config.HARDCODED)

        # --- 2. Overwrite with any matching values from incoming JSON ---
        for src, dest in config.PAYLOAD_FIELDS.items():
            value = raw.get(src)
            if value is not None and str(value).strip() != "":
                record[dest] = value

        # --- 3. Validate mandatory fields ---
        missing = [f for f in config.MANDATORY_FIELDS if not str(record.get(f, "")).strip()]
        if missing:
            result["error"] = f"Missing mandatory fields: {', '.join(missing)}"
            logger.warning(f"Row {row_idx}: {result['error']}")
            results.append(result)
            continue

        # --- 4. Build payload ---
        payload = {"customerV2s": [record]}
        result["payload_sent"] = payload

        query_params = {
            "sharedSetCode": record["sharedSetCode"],
            "customerCode":  record["customerCode"],
            "viewUri":       QAD_VIEW_URI,
        }
        headers = {
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {token}",
        }

        # --- 5. POST (retry once on 401) ---
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
                logger.error(f"Row {row_idx} ({record['customerCode']}): {result['error']}")
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
                        f"Row {row_idx} ✅ {record['customerCode']} | "
                        f"changeStatus={result['status']['changeStatus']} "
                        f"isActive={result['status']['isActive']}"
                    )
                except Exception as e:
                    logger.warning(f"Row {row_idx} ✅ {record['customerCode']} — could not parse response: {e}")
                break

            elif resp.status_code == 401 and attempt == 0:
                logger.warning(f"Row {row_idx}: 401 — refreshing token and retrying")
                token = token_manager.refresh()
                headers["Authorization"] = f"Bearer {token}"

            else:
                result["error"] = f"HTTP {resp.status_code}: {resp.text[:500]}"
                logger.error(f"Row {row_idx} ({record['customerCode']}): {result['error']}")
                break

        results.append(result)

    return results