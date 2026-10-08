from decimal import Decimal


AUTO_APPROVAL_LIMIT = Decimal("10000")


def determine_approval(
    invoice,
    risk_result: dict,
):
    if risk_result["risk_level"] == "high":
        return {
            "approval_required": False,
            "approval_status": "blocked",
            "reason": "High-risk invoice cannot proceed automatically.",
        }

    if risk_result["risk_level"] == "medium":
        return {
            "approval_required": True,
            "approval_status": "pending",
            "reason": "Medium-risk invoice requires human approval.",
        }

    if invoice.total_amount > AUTO_APPROVAL_LIMIT:
        return {
            "approval_required": True,
            "approval_status": "pending",
            "reason": (
                f"Invoice amount {invoice.total_amount} exceeds "
                f"the automatic approval limit of "
                f"{AUTO_APPROVAL_LIMIT}."
            ),
        }

    return {
        "approval_required": False,
        "approval_status": "approved",
        "reason": (
            f"Low-risk invoice is within the automatic approval "
            f"limit of {AUTO_APPROVAL_LIMIT}."
        ),
    }