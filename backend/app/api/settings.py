"""
app/api/settings.py
----------------------
GET  /api/config
POST /api/save-config
POST /api/test-connection

Ported from the existing main.py almost unchanged — this part of the design
was already fine, it just needed to move out of the monolith.
"""

import json

import requests
from fastapi import APIRouter
from pydantic import BaseModel

from app.config import CONFIG_PATH, reload_config

router = APIRouter()


class SaveConfigRequest(BaseModel):
    base_url: str
    client_id: str
    username: str
    password: str
    grant_type: str
    folders: dict = {}


def _read_config_file() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def _write_config_file(data: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)


@router.get("/api/config")
def api_get_config():
    try:
        return {"ok": True, "config": _read_config_file()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/api/save-config")
def api_save_config(req: SaveConfigRequest):
    try:
        data = _read_config_file()
        data["qad"]["base_url"] = req.base_url.strip()
        data["qad"]["auth"]["client_id"] = req.client_id.strip()
        data["qad"]["auth"]["username"] = req.username.strip()
        data["qad"]["auth"]["password"] = req.password.strip()
        data["qad"]["auth"]["grant_type"] = req.grant_type.strip()

        for key, path in req.folders.items():
            if path.strip():
                data["folders"][key] = path.strip()

        _write_config_file(data)
        reload_config()
        return {"ok": True, "message": "Config saved and reloaded."}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/api/test-connection")
def api_test_connection():
    try:
        cfg = _read_config_file()
        url = f"{cfg['qad']['base_url']}/oauth/token"
        resp = requests.post(url, data=cfg["qad"]["auth"], timeout=10)
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if not token:
            return {"ok": False, "error": "No access_token in response"}
        return {"ok": True, "message": "Connection successful"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
