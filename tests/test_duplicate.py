from app.services.duplicate import check_exact_duplicate


result = check_exact_duplicate(
    supplier_id="SUP-011",
    invoice_number="APEX-2026-8001",
)

print("\nDUPLICATE CHECK")
print(result)