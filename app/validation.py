"""Business-rule checks that make extracted data safe to push into an ERP.

An LLM or a regex can read a number wrongly without any error. These checks catch
that by verifying the arithmetic on the invoice itself.
"""
from decimal import Decimal
from typing import List

from app.schemas import Invoice

REQUIRED_FIELDS = ("invoice_number", "invoice_date", "vendor_name", "total")
TOLERANCE = Decimal("0.01")


def _close(a: Decimal, b: Decimal) -> bool:
    return abs(a - b) <= TOLERANCE


def validate_invoice(invoice: Invoice) -> List[str]:
    """Return a list of human-readable warnings (empty list means all checks passed)."""
    warnings: List[str] = []

    for name in REQUIRED_FIELDS:
        if getattr(invoice, name) in (None, ""):
            warnings.append(f"Missing required field: {name}")

    for index, item in enumerate(invoice.line_items, start=1):
        expected = item.quantity * item.unit_price
        if not _close(expected, item.amount):
            warnings.append(
                f"Line {index} ('{item.description}'): quantity x unit price = "
                f"{expected} but amount is {item.amount}"
            )

    if invoice.line_items and invoice.subtotal is not None:
        items_sum = sum((i.amount for i in invoice.line_items), Decimal("0"))
        if not _close(items_sum, invoice.subtotal):
            warnings.append(
                f"Line items add up to {items_sum} but subtotal is {invoice.subtotal}"
            )

    if invoice.subtotal is not None and invoice.total is not None:
        expected_total = invoice.subtotal + (invoice.tax or Decimal("0"))
        if not _close(expected_total, invoice.total):
            warnings.append(
                f"Subtotal + tax = {expected_total} but total is {invoice.total}"
            )

    if invoice.invoice_date and invoice.due_date and invoice.due_date < invoice.invoice_date:
        warnings.append("Due date is before the invoice date")

    return warnings
