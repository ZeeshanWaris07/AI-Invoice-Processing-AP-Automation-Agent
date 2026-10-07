import psycopg

from app.config import DATABASE_URL


def get_connection():
    return psycopg.connect(DATABASE_URL)


def get_supplier(supplier_id: str):
    query = """
        SELECT
            supplier_id,
            supplier_name,
            approved
        FROM suppliers
        WHERE supplier_id = %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (supplier_id,))
            row = cur.fetchone()

    if not row:
        return None

    return {
        "supplier_id": row[0],
        "supplier_name": row[1],
        "approved": row[2],
    }


def get_purchase_order(po_id: str):
    query = """
        SELECT
            po_id,
            supplier_id,
            order_date,
            status
        FROM purchase_orders
        WHERE po_id = %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (po_id,))
            row = cur.fetchone()

    if not row:
        return None

    return {
        "po_id": row[0],
        "supplier_id": row[1],
        "order_date": row[2],
        "status": row[3],
    }


def get_purchase_order_items(po_id: str):
    query = """
        SELECT
            po_item_id,
            po_id,
            line_no,
            item_name,
            unit,
            quantity_ordered,
            unit_price
        FROM purchase_order_items
        WHERE po_id = %s
        ORDER BY line_no
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (po_id,))
            rows = cur.fetchall()

    return [
        {
            "po_item_id": row[0],
            "po_id": row[1],
            "line_no": row[2],
            "item_name": row[3],
            "unit": row[4],
            "quantity_ordered": row[5],
            "unit_price": row[6],
        }
        for row in rows
    ]


def get_goods_receipts(po_id: str):
    query = """
        SELECT
            gr.receipt_id,
            gr.po_id,
            gr.receipt_date,
            gri.receipt_item_id,
            gri.po_item_id,
            gri.quantity_received
        FROM goods_receipts gr
        JOIN goods_receipt_items gri
            ON gr.receipt_id = gri.receipt_id
        WHERE gr.po_id = %s
        ORDER BY gr.receipt_date, gri.po_item_id
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (po_id,))
            rows = cur.fetchall()

    return [
        {
            "receipt_id": row[0],
            "po_id": row[1],
            "receipt_date": row[2],
            "receipt_item_id": row[3],
            "po_item_id": row[4],
            "quantity_received": row[5],
        }
        for row in rows
    ]


def find_similar_invoices(
    supplier_id: str,
    po_id: str | None,
    total_amount,
    invoice_date,
):
    query = """
        SELECT
            invoice_id,
            supplier_id,
            po_id,
            invoice_number,
            invoice_date,
            total_amount,
            status
        FROM invoices
        WHERE supplier_id = %s
          AND total_amount = %s
          AND invoice_date BETWEEN %s - INTERVAL '7 days'
                               AND %s + INTERVAL '7 days'
        ORDER BY invoice_date
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    supplier_id,
                    total_amount,
                    invoice_date,
                    invoice_date,
                ),
            )
            rows = cur.fetchall()

    return [
        {
            "invoice_id": row[0],
            "supplier_id": row[1],
            "po_id": row[2],
            "invoice_number": row[3],
            "invoice_date": row[4],
            "total_amount": row[5],
            "status": row[6],
        }
        for row in rows
    ]