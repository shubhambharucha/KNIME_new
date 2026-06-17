"""
app/core/registry.py
--------------------
Central registry of all entities: maps entity name → config module + loader module.
"""

from typing import Any

# Import all entity modules
from app.entities import customer

# Registry: entity_name → {"config": config_module, "loader": loader_module}
ENTITY_MAP: dict[str, dict[str, Any]] = {
    "Customer": {
        "config": customer.config,
        "loader": customer.loader,
    },
    # Future entities go here:
    # "Supplier": {"config": supplier.config, "loader": supplier.loader},
    # "GCM": {"config": gcm.config, "loader": gcm.loader},
    # etc.
}


def get_entity(entity_name: str) -> dict[str, Any] | None:
    """Retrieve entity config + loader by name (case-insensitive)."""
    return ENTITY_MAP.get(entity_name) or ENTITY_MAP.get(entity_name.lower())


def list_entities() -> list[str]:
    """Return all registered entity names."""
    return list(ENTITY_MAP.keys())