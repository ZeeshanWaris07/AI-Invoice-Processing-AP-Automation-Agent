from langgraph.graph import StateGraph, START, END

from app.state import InvoiceState
from app.agents.extractor import extract_invoice
from app.services.validation import validate_invoice
from app.services.retrieval import get_po_context
from app.services.matching import match_invoice
from app.services.duplicate import check_exact_duplicate


def extract_node(state: InvoiceState):
    invoice = extract_invoice(state["invoice_path"])

    return {
        "extracted_invoice": invoice.model_dump()
    }


def validation_node(state: InvoiceState):
    invoice_data = state["extracted_invoice"]

    from app.agents.extractor import ExtractedInvoice

    invoice = ExtractedInvoice.model_validate(invoice_data)

    result = validate_invoice(invoice)

    return {
        "validation_result": result
    }


def validation_router(state: InvoiceState):
    if state["validation_result"]["valid"]:
        return "valid"

    return "invalid"


def supplier_node(state: InvoiceState):
    invoice = state["extracted_invoice"]

    supplier_id = invoice.get("supplier_id")

    return {
        "supplier_id": supplier_id
    }


def duplicate_node(state: InvoiceState):
    invoice = state["extracted_invoice"]

    result = check_exact_duplicate(
        supplier_id=state["supplier_id"],
        invoice_number=invoice["invoice_number"],
    )

    return {
        "duplicate_result": result
    }


def duplicate_router(state: InvoiceState):
    if state["duplicate_result"]["is_duplicate"]:
        return "duplicate"

    return "new"


def po_retrieval_node(state: InvoiceState):
    invoice = state["extracted_invoice"]

    po_id = invoice.get("po_number")

    if not po_id:
        return {
            "error": "Invoice does not contain a PO number",
            "purchase_order": None,
            "goods_receipts": [],
        }

    context = get_po_context(po_id)

    if not context:
        return {
            "po_id": po_id,
            "purchase_order": None,
            "goods_receipts": [],
            "error": "Purchase order not found",
        }

    return {
        "po_id": po_id,
        "purchase_order": context["purchase_order"],
        "goods_receipts": context["goods_receipts"],
    }


def po_router(state: InvoiceState):
    if state.get("purchase_order") is None:
        return "missing"

    return "found"


def matching_node(state: InvoiceState):
    from app.agents.extractor import ExtractedInvoice

    invoice = ExtractedInvoice.model_validate(
        state["extracted_invoice"]
    )

    po_context = get_po_context(state["po_id"])

    result = match_invoice(
        invoice,
        po_context,
    )

    return {
        "matching_result": result
    }


def matching_router(state: InvoiceState):
    if state["matching_result"]["matched"]:
        return "matched"

    return "exception"


def exception_node(state: InvoiceState):
    return {
        "exception_result": {
            "status": "open",
            "reason": (
                state.get("error")
                or state.get("matching_result", {}).get("exceptions")
                or state.get("duplicate_result", {}).get("reason")
                or state.get("validation_result", {}).get("errors")
            ),
        },
        "final_status": "exception",
    }


def approved_node(state: InvoiceState):
    return {
        "final_status": "matched"
    }


builder = StateGraph(InvoiceState)

builder.add_node("extract", extract_node)
builder.add_node("validation", validation_node)
builder.add_node("supplier", supplier_node)
builder.add_node("duplicate", duplicate_node)
builder.add_node("po_retrieval", po_retrieval_node)
builder.add_node("matching", matching_node)
builder.add_node("exception", exception_node)
builder.add_node("approved", approved_node)

builder.add_edge(START, "extract")
builder.add_edge("extract", "validation")

builder.add_conditional_edges(
    "validation",
    validation_router,
    {
        "valid": "supplier",
        "invalid": "exception",
    },
)

builder.add_edge("supplier", "duplicate")

builder.add_conditional_edges(
    "duplicate",
    duplicate_router,
    {
        "duplicate": "exception",
        "new": "po_retrieval",
    },
)

builder.add_conditional_edges(
    "po_retrieval",
    po_router,
    {
        "missing": "exception",
        "found": "matching",
    },
)

builder.add_conditional_edges(
    "matching",
    matching_router,
    {
        "matched": "approved",
        "exception": "exception",
    },
)

builder.add_edge("exception", END)
builder.add_edge("approved", END)

graph = builder.compile()