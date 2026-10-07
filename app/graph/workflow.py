from langgraph.graph import StateGraph, START, END

from app.state import InvoiceState
from app.agents.extractor import extract_invoice
from app.agents.extractor import ExtractedInvoice
from app.services.validation import validate_invoice
from app.services.retrieval import get_po_context
from app.services.matching import match_invoice
from app.services.duplicate import check_exact_duplicate
from app.tools.database import find_supplier_by_name


def extract_node(state: InvoiceState):
    invoice = extract_invoice(state["invoice_path"])

    return {
        "extracted_invoice": invoice.model_dump()
    }


def validation_node(state: InvoiceState):
    invoice = ExtractedInvoice.model_validate(
        state["extracted_invoice"]
    )

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

    supplier_name = invoice.get("supplier_name")

    if not supplier_name:
        return {
            "supplier_id": None,
            "error": "Invoice does not contain a supplier name",
        }

    supplier = find_supplier_by_name(supplier_name)

    if not supplier:
        return {
            "supplier_id": None,
            "error": f"Supplier not found: {supplier_name}",
        }

    if supplier.get("ambiguous"):
        return {
            "supplier_id": None,
            "error": f"Multiple suppliers found for: {supplier_name}",
        }

    return {
        "supplier_id": supplier["supplier_id"],
        "error": None,
    }


def supplier_router(state: InvoiceState):
    if state.get("supplier_id") is None:
        return "missing"

    return "found"


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
            "po_id": None,
            "po_context": None,
            "purchase_order": None,
            "goods_receipts": [],
            "error": "Invoice does not contain a PO number",
        }

    context = get_po_context(po_id)

    if not context:
        return {
            "po_id": po_id,
            "po_context": None,
            "purchase_order": None,
            "goods_receipts": [],
            "error": f"Purchase order not found: {po_id}",
        }

    return {
        "po_id": po_id,
        "po_context": context,
        "purchase_order": context["purchase_order"],
        "goods_receipts": context["goods_receipts"],
        "error": None,
    }


def po_router(state: InvoiceState):
    if state.get("po_context") is None:
        return "missing"

    return "found"


def matching_node(state: InvoiceState):
    invoice = ExtractedInvoice.model_validate(
        state["extracted_invoice"]
    )

    result = match_invoice(
        invoice,
        state["po_context"],
    )

    return {
        "matching_result": result
    }


def matching_router(state: InvoiceState):
    if state["matching_result"]["matched"]:
        return "matched"

    return "exception"


def exception_node(state: InvoiceState):
    reason = (
        state.get("error")
        or state.get("matching_result", {}).get("exceptions")
        or state.get("duplicate_result", {}).get("reason")
        or state.get("validation_result", {}).get("errors")
    )

    return {
        "exception_result": {
            "status": "open",
            "reason": reason,
        },
        "final_status": "exception",
    }


def matched_node(state: InvoiceState):
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
builder.add_node("matched", matched_node)

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

builder.add_conditional_edges(
    "supplier",
    supplier_router,
    {
        "found": "duplicate",
        "missing": "exception",
    },
)

builder.add_conditional_edges(
    "duplicate",
    duplicate_router,
    {
        "new": "po_retrieval",
        "duplicate": "exception",
    },
)

builder.add_conditional_edges(
    "po_retrieval",
    po_router,
    {
        "found": "matching",
        "missing": "exception",
    },
)

builder.add_conditional_edges(
    "matching",
    matching_router,
    {
        "matched": "matched",
        "exception": "exception",
    },
)

builder.add_edge("matched", END)
builder.add_edge("exception", END)

graph = builder.compile()