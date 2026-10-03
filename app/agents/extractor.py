from datetime import date
from decimal import Decimal
from app.tools.invoice import extract_pdf_text
from app.llm import llm
from pydantic import BaseModel, Field


class InvoiceItem(BaseModel):
    line_no: int
    item_name: str
    description: str | None = None
    unit: str
    quantity: Decimal
    unit_price: Decimal
    tax_amount: Decimal = Decimal("0")
    line_total: Decimal


class ExtractedInvoice(BaseModel):
    invoice_number: str
    supplier_name: str
    supplier_id: str | None = None
    invoice_date: date
    due_date: date | None = None
    po_number: str | None = None
    currency: str
    items: list[InvoiceItem]
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal


extraction_llm = llm.with_structured_output(ExtractedInvoice)

def extract_invoice(invoice_path):
    text = extract_pdf_text(invoice_path)

    prompt = f"""
Extract the invoice information from the document below.

Rules:
- Extract only information explicitly present in the document.
- Do not invent missing values.
- Preserve quantities and prices exactly.
- Calculate nothing yourself unless the document explicitly provides the value.
- If supplier_id is not present, return null.
- If PO number is not present, return null.
- Return the result using the required structured schema.

For each invoice line:

- item_name: Extract the short product/item name.
- description: Extract the detailed product description separately.
- Do not combine the description with item_name.
- If the document does not clearly provide a separate description, use null.

Invoice document:

{text}
"""

    return extraction_llm.invoke(prompt)