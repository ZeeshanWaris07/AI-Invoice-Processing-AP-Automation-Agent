from typing import TypedDict


class InvoiceState(TypedDict, total=False):
    invoice_id: str
    invoice_path: str

    extracted_invoice: dict

    supplier_id: str | None

    validation_result: dict
    duplicate_result: dict

    po_id: str | None
    purchase_order: dict | None
    goods_receipts: list[dict]

    matching_result: dict

    risk_result: dict

    exception_result: dict

    approval_required: bool
    approval_result: dict | None

    bookkeeping_result: dict | None
    payment_result: dict | None

    final_status: str
    error: str | None