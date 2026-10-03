from decimal import Decimal


def validate_invoice(invoice):
    errors = []

    if not invoice.invoice_number:
        errors.append("Missing invoice number")

    if not invoice.supplier_name:
        errors.append("Missing supplier name")

    if not invoice.invoice_date:
        errors.append("Missing invoice date")

    if not invoice.currency:
        errors.append("Missing currency")

    if not invoice.items:
        errors.append("Invoice contains no line items")

    calculated_subtotal = Decimal("0")

    for item in invoice.items:
        if item.quantity <= 0:
            errors.append(
                f"Line {item.line_no}: quantity must be greater than zero"
            )

        if item.unit_price < 0:
            errors.append(
                f"Line {item.line_no}: unit price cannot be negative"
            )

        expected_line_total = (
            item.quantity * item.unit_price + item.tax_amount
        )

        if expected_line_total != item.line_total:
            errors.append(
                f"Line {item.line_no}: line total mismatch"
            )

        calculated_subtotal += item.quantity * item.unit_price

    if calculated_subtotal != invoice.subtotal:
        errors.append(
            "Invoice subtotal does not match the sum of line items"
        )

    calculated_total = invoice.subtotal + invoice.tax_amount

    if calculated_total != invoice.total_amount:
        errors.append(
            "Invoice total does not match subtotal plus tax"
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }