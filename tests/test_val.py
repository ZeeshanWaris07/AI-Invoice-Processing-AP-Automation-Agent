from app.agents.extractor import extract_invoice
from app.services.validation import validate_invoice

invoice_path = "invoices/invoice_001.pdf"

invoice = extract_invoice(invoice_path)

print("\nEXTRACTED INVOICE")
print(invoice.model_dump())

result = validate_invoice(invoice)

print("\nVALIDATION RESULT")
print(result)