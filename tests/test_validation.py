from datetime import date
from decimal import Decimal

from app.schemas import Invoice, LineItem
from app.validation import validate_invoice


def good_invoice(**overrides):
    data = dict(
        invoice_number="INV-1",
        invoice_date=date(2026, 1, 10),
        due_date=date(2026, 2, 10),
        vendor_name="Vendor",
        line_items=[
            LineItem(description="A", quantity=2, unit_price=Decimal("5.00"), amount=Decimal("10.00")),
            LineItem(description="B", quantity=1, unit_price=Decimal("20.00"), amount=Decimal("20.00")),
        ],
        subtotal=Decimal("30.00"),
        tax=Decimal("3.00"),
        total=Decimal("33.00"),
    )
    data.update(overrides)
    return Invoice(**data)


def test_consistent_invoice_has_no_warnings():
    assert validate_invoice(good_invoice()) == []


def test_missing_required_fields_are_reported():
    warnings = validate_invoice(Invoice())
    assert any("invoice_number" in w for w in warnings)
    assert any("total" in w for w in warnings)


def test_wrong_line_amount_is_reported():
    items = [LineItem(description="A", quantity=2, unit_price=Decimal("5.00"), amount=Decimal("11.00"))]
    warnings = validate_invoice(good_invoice(line_items=items, subtotal=Decimal("11.00"), total=Decimal("14.00")))
    assert any("Line 1" in w for w in warnings)


def test_line_items_not_matching_subtotal_is_reported():
    warnings = validate_invoice(good_invoice(subtotal=Decimal("99.00"), total=Decimal("102.00")))
    assert any("subtotal" in w.lower() for w in warnings)


def test_wrong_total_is_reported():
    warnings = validate_invoice(good_invoice(total=Decimal("40.00")))
    assert any("total" in w.lower() for w in warnings)


def test_rounding_within_one_cent_is_accepted():
    assert validate_invoice(good_invoice(total=Decimal("33.01"))) == []


def test_due_date_before_invoice_date_is_reported():
    warnings = validate_invoice(good_invoice(due_date=date(2025, 12, 1)))
    assert any("Due date" in w for w in warnings)
