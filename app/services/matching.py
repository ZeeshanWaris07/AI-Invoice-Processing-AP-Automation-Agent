from decimal import Decimal


PRICE_TOLERANCE = Decimal("0.01")


def _normalize(value):
    return str(value).strip().lower()


def match_invoice(invoice, po_context):
    exceptions = []
    line_results = []

    if not po_context:
        return {
            "matched": False,
            "exceptions": ["Purchase order not found"],
            "line_results": [],
        }

    purchase_order = po_context["purchase_order"]
    supplier = po_context["supplier"]
    po_items = po_context["items"]

    if invoice.supplier_id:
        if invoice.supplier_id != supplier["supplier_id"]:
            exceptions.append(
                f"Supplier mismatch: invoice supplier {invoice.supplier_id} "
                f"does not match PO supplier {supplier['supplier_id']}"
            )

    for invoice_item in invoice.items:
        matching_items = [
            item
            for item in po_items
            if _normalize(item["item_name"]) == _normalize(invoice_item.item_name)
            and _normalize(item["unit"]) == _normalize(invoice_item.unit)
        ]

        if not matching_items:
            line_results.append({
                "invoice_line": invoice_item.line_no,
                "status": "exception",
                "reason": "No matching PO item found",
            })
            continue

        if len(matching_items) > 1:
            line_results.append({
                "invoice_line": invoice_item.line_no,
                "status": "exception",
                "reason": "Multiple matching PO items found",
            })
            continue

        po_item = matching_items[0]

        line_exceptions = []

        if invoice_item.quantity > po_item["quantity_ordered"]:
            line_exceptions.append(
                f"Invoice quantity {invoice_item.quantity} exceeds "
                f"ordered quantity {po_item['quantity_ordered']}"
            )

        if invoice_item.quantity > po_item["quantity_received"]:
            line_exceptions.append(
                f"Invoice quantity {invoice_item.quantity} exceeds "
                f"received quantity {po_item['quantity_received']}"
            )

        price_difference = abs(
            invoice_item.unit_price - po_item["unit_price"]
        )

        if price_difference > PRICE_TOLERANCE:
            line_exceptions.append(
                f"Invoice unit price {invoice_item.unit_price} does not "
                f"match PO unit price {po_item['unit_price']}"
            )

        line_results.append({
            "invoice_line": invoice_item.line_no,
            "po_item_id": po_item["po_item_id"],
            "item_name": po_item["item_name"],
            "invoice_quantity": invoice_item.quantity,
            "ordered_quantity": po_item["quantity_ordered"],
            "received_quantity": po_item["quantity_received"],
            "invoice_unit_price": invoice_item.unit_price,
            "po_unit_price": po_item["unit_price"],
            "status": "matched" if not line_exceptions else "exception",
            "exceptions": line_exceptions,
        })

        exceptions.extend(line_exceptions)

    matched = len(exceptions) == 0 and all(
        result["status"] == "matched"
        for result in line_results
    )

    return {
        "matched": matched,
        "po_id": purchase_order["po_id"],
        "supplier_id": supplier["supplier_id"],
        "exceptions": exceptions,
        "line_results": line_results,
    }