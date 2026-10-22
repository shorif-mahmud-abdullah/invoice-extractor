from datetime import date
from decimal import Decimal
from pathlib import Path

from app.extractors.rules import extract_with_rules

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def read(name):
    return (SAMPLES / name).read_text()


def test_header_fields_are_extracted():
    invoice = extract_with_rules(read("invoice_001.txt"))
    assert invoice.invoice_number == "INV-2026-0042"
    assert invoice.invoice_date == date(2026, 9, 14)
    assert invoice.due_date == date(2026, 10, 14)
    assert invoice.vendor_name == "Northwind Supplies Ltd"
    assert invoice.bill_to == "Acme Construction Co."
    assert invoice.currency == "USD"


def test_line_items_and_totals_with_pipe_table():
    invoice = extract_with_rules(read("invoice_001.txt"))
    assert [i.description for i in invoice.line_items] == [
        "Cement bags (50kg)",
        "Steel rebar 12mm",
        "Safety helmets",
    ]
    assert invoice.line_items[0].quantity == Decimal("100")
    assert invoice.line_items[0].unit_price == Decimal("8.50")
    assert invoice.subtotal == Decimal("1250.00")
    assert invoice.tax == Decimal("125.00")
    assert invoice.total == Decimal("1375.00")


def test_plain_spaced_table_and_thousands_separator():
    invoice = extract_with_rules(read("invoice_002.txt"))
    assert len(invoice.line_items) == 2
    assert invoice.line_items[0].amount == Decimal("1600.00")
    assert invoice.total == Decimal("1890.00")


def test_unrelated_text_gives_an_empty_invoice():
    invoice = extract_with_rules("Hello, this is not an invoice.")
    assert invoice.line_items == []
    assert invoice.total is None
