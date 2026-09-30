from collections import defaultdict

from app.tools.database import (
    get_purchase_order,
    get_purchase_order_items,
    get_goods_receipts,
    get_supplier,
)


def get_po_context(po_id: str):
    purchase_order = get_purchase_order(po_id)

    if not purchase_order:
        return None

    supplier = get_supplier(purchase_order["supplier_id"])
    items = get_purchase_order_items(po_id)
    receipts = get_goods_receipts(po_id)

    received_quantities = defaultdict(int)

    for receipt in receipts:
        received_quantities[receipt["po_item_id"]] += receipt["quantity_received"]

    for item in items:
        item["quantity_received"] = received_quantities[item["po_item_id"]]
        item["quantity_remaining"] = (
            item["quantity_ordered"] - item["quantity_received"]
        )

    return {
        "purchase_order": purchase_order,
        "supplier": supplier,
        "items": items,
        "goods_receipts": receipts,
    }