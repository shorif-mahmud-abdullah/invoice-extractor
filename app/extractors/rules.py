"""Deterministic, dependency-free extractor for simple text invoices.

It works offline with no API key, so the demo and the test suite run anywhere.
Messy or unusual layouts are what the LLM extractor is for.
"""
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional

from app.schemas import Invoice, LineItem

_ITEM = re.compile(
    r"^(?P<desc>.+?)\s+(?P<qty>\d+(?:\.\d+)?)\s+"
    r"(?P<unit>[\d,]+\.\d{2})\s+(?P<amount>[\d,]+\.\d{2})$"
)


def _money(text: str) -> Optional[Decimal]:
    try:
        return Decimal(text.replace(",", "").replace("$", "").strip())
    except InvalidOperation:
        return None


def _date(text: str) -> Optional[date]:
    try:
        return date.fromisoformat(text.strip())
    except ValueError:
        return None


def _field(text: str, label: str) -> Optional[str]:
    match = re.search(rf"^{label}\s*:\s*(.+)$", text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else None


def extract_with_rules(text: str) -> Invoice:
    # Tables can come out as "a | 1 | 2.00 | 2.00" or as plain spaced columns.
    normalized = text.replace("|", " ")

    line_items = []
    for line in normalized.splitlines():
        match = _ITEM.match(line.strip())
        if match:
            line_items.append(
                LineItem(
                    description=re.sub(r"\s+", " ", match["desc"]).strip(),
                    quantity=Decimal(match["qty"]),
                    unit_price=_money(match["unit"]),
                    amount=_money(match["amount"]),
                )
            )

    tax_text = _field(text, r"Tax(?:\s*\([^)]*\))?")
    subtotal_text = _field(text, "Subtotal")
    total_text = _field(text, "Total")
    invoice_date = _field(text, "Date") or _field(text, "Invoice Date")
    due_date = _field(text, "Due Date")

    return Invoice(
        invoice_number=_field(text, "Invoice\\s*(?:No|Number|#)\\.?"),
        invoice_date=_date(invoice_date) if invoice_date else None,
        due_date=_date(due_date) if due_date else None,
        vendor_name=_field(text, "Vendor") or _field(text, "From"),
        bill_to=_field(text, "Bill To"),
        currency=_field(text, "Currency"),
        line_items=line_items,
        subtotal=_money(subtotal_text) if subtotal_text else None,
        tax=_money(tax_text) if tax_text else None,
        total=_money(total_text) if total_text else None,
    )
