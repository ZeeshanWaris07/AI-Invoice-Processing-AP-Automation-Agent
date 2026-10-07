from app.tools.database import (
    find_similar_invoices,
)


def check_possible_duplicate(invoice, supplier_id: str):
    candidates = find_similar_invoices(
        supplier_id=supplier_id,
        po_id=invoice.po_number,
        total_amount=invoice.total_amount,
        invoice_date=invoice.invoice_date,
    )

    results = []

    for candidate in candidates:
        score = 0
        signals = []

        if candidate["po_id"] and invoice.po_number:
            if candidate["po_id"] == invoice.po_number:
                score += 30
                signals.append("same purchase order")

        if candidate["total_amount"] == invoice.total_amount:
            score += 30
            signals.append("same total amount")

        date_difference = abs(
            (candidate["invoice_date"] - invoice.invoice_date).days
        )

        if date_difference == 0:
            score += 20
            signals.append("same invoice date")
        elif date_difference <= 7:
            score += 10
            signals.append("invoice dates within 7 days")

        if score >= 70:
            classification = "likely_duplicate"
        elif score >= 50:
            classification = "possible_duplicate"
        else:
            classification = "unlikely_duplicate"

        results.append({
            "existing_invoice_id": candidate["invoice_id"],
            "existing_invoice_number": candidate["invoice_number"],
            "existing_status": candidate["status"],
            "score": score,
            "classification": classification,
            "signals": signals,
        })

    likely_duplicates = [
        result
        for result in results
        if result["classification"] == "likely_duplicate"
    ]

    possible_duplicates = [
        result
        for result in results
        if result["classification"] == "possible_duplicate"
    ]

    return {
        "is_duplicate": bool(likely_duplicates),
        "requires_review": bool(possible_duplicates),
        "candidates": results,
    }