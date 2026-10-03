import json

from app.agents.extractor import extract_invoice
from app.services.retrieval import get_po_context
from app.services.matching import match_invoice


invoice_path = "invoices/invoice_001.pdf"

invoice = extract_invoice(invoice_path)

print()

po_context = get_po_context(invoice.po_number)

print("\nINVOICE ITEMS")
for item in invoice.items:
    print(
        "invoice:",
        repr(item.item_name),
        repr(item.unit)
    )

print("\nPO ITEMS")
for item in po_context["items"]:
    print(
        "PO:",
        repr(item["item_name"]),
        repr(item["unit"])
    )

result = match_invoice(invoice, po_context)

print("\nMATCHING RESULT")
print(json.dumps(result, indent=4, default=str))