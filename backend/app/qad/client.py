"""
app/qad/client.py
-------------------
Generic request helpers + a retry wrapper, so entity loaders don't each
reimplement "try the call, refresh token on 401, try once more."
"""

from typing import Callable

import requests

from app.config import CONFIG
from app.qad.auth import TokenExpired, TokenManager


def qad_url(path: str) -> str:
    return f"{CONFIG['qad']['base_url']}{path}"


def with_token_retry(tm: TokenManager, call: Callable[[str], tuple]) -> tuple:
    """
    call(token) must return (success: bool, error_msg: str) and raise
    TokenExpired on a 401. Retries once after refreshing the token.
    """
    for attempt in range(2):
        try:
            return call(tm.get())
        except TokenExpired:
            if attempt == 0:
                tm.refresh()
                continue
            return False, "Token refresh failed — unauthorised"
        except requests.RequestException as e:
            return False, f"Network error: {e}"
    return False, "Unknown error"
