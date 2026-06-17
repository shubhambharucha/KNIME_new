"""
app/core/registry.py
-----------------------
Maps entity id -> { validator, loader, config }. Only Customer is wired so far
since it's the only entity whose row-level logic was ported. Add an entity by
filling in its three-file folder under entities/ and registering it here —
that's the entire "add a new entity" workflow.
"""

from app.entities.customer import config as customer_config
from app.entities.customer import loader as customer_loader
from app.entities.customer import validator as customer_validator

ENTITY_MAP: dict[str, dict] = {
    "Customer": {
        "validate_row": customer_validator.validate_row,
        "load_row": customer_loader.load_row,
        "config": customer_config,
    },
    # TODO: port these the same way once their existing scripts are available.
    # Each just needs entities/<name>/{config,validator,loader}.py following
    # the Customer pattern, then an entry here.
    "Supplier": None,
    "GCM": None,
    "BR": None,
    "Customer_Item": None,
    "ProductionOrder": None,
    "PurchaseOrder": None,
    "SalesOrder": None,
    "Supplier_Item": None,
    "SupplierPriceList": None,
}


def is_implemented(entity: str) -> bool:
    return ENTITY_MAP.get(entity) is not None
