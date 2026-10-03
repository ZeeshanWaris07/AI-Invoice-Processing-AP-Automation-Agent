import json

from app.agents.extractor import extract_invoice
from app.services.retrieval import get_po_context
from app.services.matching import match_invoice


invoice_path = "invoices/invoice_001.pdf"

invoice = extract_invoice(invoice_path)

po_context = get_po_context(invoice.po_number)

result = match_invoice(invoice, po_context)

print("\nMATCHING RESULT")
print(json.dumps(result, indent=4, default=str))