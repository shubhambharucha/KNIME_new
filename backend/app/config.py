"""
app/config.py
--------------
Loads config.json (QAD connection + folder paths, kept for legacy entities
that haven't been ported yet). Ported unchanged from the old Backend/config.py
so existing behaviour (and your existing config.json) keeps working.
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")


def load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


CONFIG = load_config()


def reload_config() -> dict:
    """Hot-reload CONFIG in place so running streams pick up new values."""
    global CONFIG
    CONFIG = load_config()
    return CONFIG


__all__ = ["CONFIG", "CONFIG_PATH", "load_config", "reload_config"]
