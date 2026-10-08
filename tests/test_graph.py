from app.graph.workflow import graph


result = graph.invoke({
    "invoice_path": "invoices/invoice_002.pdf"
})


print("\nFINAL STATUS:")
print(result.get("final_status"))

print("\nSUPPLIER ID:")
print(result.get("supplier_id"))

print("\nPO ID:")
print(result.get("po_id"))

print("\nDUPLICATE RESULT:")
print(result.get("duplicate_result"))

print("\nMATCHING RESULT:")
print(result.get("matching_result"))

print("\nEXCEPTION RESULT:")
print(result.get("exception_result"))