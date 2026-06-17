"""
app/core/events.py
--------------------
Same SSE encoding you already had in main.py — kept identical so the
frontend's existing event-parsing loop doesn't need to change.
"""

import json


def sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\r\n\r\n"


def sse_comment() -> str:
    return ": keepalive\r\n\r\n"
