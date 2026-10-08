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

def find_supplier_by_name(supplier_name: str):
    query = """
        SELECT supplier_id, supplier_name, approved
        FROM suppliers
        WHERE LOWER(TRIM(supplier_name)) = LOWER(TRIM(%s))
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (supplier_name,))
            rows = cur.fetchall()

    if len(rows) == 0:
        return None

    if len(rows) > 1:
        return {
            "ambiguous": True,
            "suppliers": [
                {
                    "supplier_id": row[0],
                    "supplier_name": row[1],
                    "approved": row[2],
                }
                for row in rows
            ],
        }

    row = rows[0]

    return {
        "supplier_id": row[0],
        "supplier_name": row[1],
        "approved": row[2],
    }

import uuid


def save_processed_invoice(
    invoice_id : str,
    invoice,
    supplier_id: str,
    po_id: str,
    matching_result: dict,
    source_file: str | None = None,
):

    line_results = {
        result["invoice_line"]: result
        for result in matching_result["line_results"]
    }

    invoice_query = """
        INSERT INTO invoices (
            invoice_id,
            supplier_id,
            po_id,
            invoice_number,
            invoice_date,
            due_date,
            subtotal,
            tax_amount,
            total_amount,
            currency,
            status,
            source_file
        )
        VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        )
        RETURNING invoice_id
    """

    item_query = """
        INSERT INTO invoice_items (
            invoice_id,
            po_item_id,
            line_no,
            item_name,
            unit,
            quantity,
            unit_price,
            tax_amount,
            line_total
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                invoice_query,
                (
                    invoice_id,
                    supplier_id,
                    po_id,
                    invoice.invoice_number,
                    invoice.invoice_date,
                    invoice.due_date,
                    invoice.subtotal,
                    invoice.tax_amount,
                    invoice.total_amount,
                    invoice.currency,
                    "matched",
                    source_file,
                ),
            )

            invoice_id = cur.fetchone()[0]

            for item in invoice.items:
                match_result = line_results.get(item.line_no)

                po_item_id = None

                if match_result:
                    po_item_id = match_result.get("po_item_id")

                cur.execute(
                    item_query,
                    (
                        invoice_id,
                        po_item_id,
                        item.line_no,
                        item.item_name,
                        item.unit,
                        item.quantity,
                        item.unit_price,
                        item.tax_amount,
                        item.line_total,
                    ),
                )

    return invoice_id



def get_or_create_pending_approval(invoice_id: str):
    query = """
        SELECT
            approval_id,
            invoice_id,
            approval_status,
            requested_at
        FROM invoice_approvals
        WHERE invoice_id = %s
          AND approval_status = 'pending'
        ORDER BY requested_at DESC
        LIMIT 1
    """

    insert_query = """
        INSERT INTO invoice_approvals (
            invoice_id,
            approval_status
        )
        VALUES (%s, 'pending')
        RETURNING
            approval_id,
            invoice_id,
            approval_status,
            requested_at
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (invoice_id,))
            row = cur.fetchone()

            if row:
                return {
                    "approval_id": row[0],
                    "invoice_id": row[1],
                    "approval_status": row[2],
                    "requested_at": row[3],
                }

            cur.execute(insert_query, (invoice_id,))
            row = cur.fetchone()

    return {
        "approval_id": row[0],
        "invoice_id": row[1],
        "approval_status": row[2],
        "requested_at": row[3],
    }


def update_invoice_approval(
    approval_id: int,
    approved: bool,
    reviewer: str,
    reviewer_comment: str | None = None,
):
    approval_status = "approved" if approved else "rejected"

    query = """
        UPDATE invoice_approvals
        SET
            approval_status = %s,
            reviewed_at = CURRENT_TIMESTAMP,
            reviewer = %s,
            reviewer_comment = %s
        WHERE approval_id = %s
        RETURNING
            approval_id,
            invoice_id,
            approval_status,
            reviewed_at,
            reviewer,
            reviewer_comment
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    approval_status,
                    reviewer,
                    reviewer_comment,
                    approval_id,
                ),
            )
            row = cur.fetchone()

    if not row:
        raise ValueError(
            f"Approval record {approval_id} was not found."
        )

    return {
        "approval_id": row[0],
        "invoice_id": row[1],
        "approval_status": row[2],
        "reviewed_at": row[3],
        "reviewer": row[4],
        "reviewer_comment": row[5],
    }