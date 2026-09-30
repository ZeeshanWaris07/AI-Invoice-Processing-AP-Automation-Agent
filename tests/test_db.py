from app.services.retrieval import get_po_context


def main():
    context = get_po_context("PO-0001")

    print("\nPURCHASE ORDER")
    print(context["purchase_order"])

    print("\nSUPPLIER")
    print(context["supplier"])

    print("\nITEMS")

    for item in context["items"]:
        print(item)

    print("\nGOODS RECEIPTS")

    for receipt in context["goods_receipts"]:
        print(receipt)


if __name__ == "__main__":
    main()