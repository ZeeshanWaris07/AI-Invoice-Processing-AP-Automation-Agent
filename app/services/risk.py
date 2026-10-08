from decimal import Decimal


HIGH_VALUE_THRESHOLD = Decimal("50000")

MEDIUM_RISK_SCORE = 40
HIGH_RISK_SCORE = 70


def assess_invoice_risk(
    invoice,
    supplier_id: str,
    po_context: dict,
):
    risk_score = 0
    signals = []

    purchase_order = po_context.get("purchase_order")
    supplier = po_context.get("supplier")

    if not supplier:
        risk_score += 70
        signals.append({
            "type": "supplier_not_found",
            "severity": "high",
            "message": "Supplier could not be verified in the database.",
        })
    else:
        if not supplier["approved"]:
            risk_score += 70
            signals.append({
                "type": "unapproved_supplier",
                "severity": "high",
                "message": (
                    f"Supplier {supplier['supplier_id']} "
                    "is not approved."
                ),
            })

    if purchase_order:
        if purchase_order["supplier_id"] != supplier_id:
            risk_score += 70
            signals.append({
                "type": "supplier_po_mismatch",
                "severity": "high",
                "message": (
                    f"Resolved supplier {supplier_id} does not match "
                    f"PO supplier {purchase_order['supplier_id']}."
                ),
            })

        if purchase_order["status"].lower() != "open":
            risk_score += 40
            signals.append({
                "type": "po_not_open",
                "severity": "medium",
                "message": (
                    f"Purchase order status is "
                    f"'{purchase_order['status']}'."
                ),
            })

        if invoice.invoice_date < purchase_order["order_date"]:
            risk_score += 30
            signals.append({
                "type": "invoice_before_po",
                "severity": "medium",
                "message": "Invoice date is earlier than the PO date.",
            })

    if invoice.due_date and invoice.due_date < invoice.invoice_date:
        risk_score += 20
        signals.append({
            "type": "invalid_due_date",
            "severity": "medium",
            "message": "Invoice due date is earlier than invoice date.",
        })

    if invoice.total_amount >= HIGH_VALUE_THRESHOLD:
        risk_score += 20
        signals.append({
            "type": "high_value_invoice",
            "severity": "medium",
            "message": (
                f"Invoice total {invoice.total_amount} "
                f"exceeds the configured threshold of "
                f"{HIGH_VALUE_THRESHOLD}."
            ),
        })

    if risk_score >= HIGH_RISK_SCORE:
        risk_level = "high"
    elif risk_score >= MEDIUM_RISK_SCORE:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "requires_review": risk_level in {"medium", "high"},
        "signals": signals,
    }