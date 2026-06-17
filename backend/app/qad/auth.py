"""
app/qad/auth.py
-----------------
Identical logic to the TokenManager in your existing Customer_load.py,
just no longer copy-pasted into every entity file. One token per run,
refreshed on 401.
"""

import requests

from app.config import CONFIG


def fetch_token() -> str:
    url = f"{CONFIG['qad']['base_url']}/oauth/token"
    resp = requests.post(url, data=CONFIG["qad"]["auth"], timeout=30)
    resp.raise_for_status()
    token = resp.json().get("access_token")
    if not token:
        raise RuntimeError("OAuth response did not contain access_token")
    return token


class TokenExpired(Exception):
    pass


class TokenManager:
    """Holds one token for the run; refreshes on demand (401)."""

    def __init__(self):
        self._token: str | None = None

    def get(self) -> str:
        if self._token is None:
            self._token = fetch_token()
        return self._token

    def refresh(self) -> str:
        self._token = fetch_token()
        return self._token
