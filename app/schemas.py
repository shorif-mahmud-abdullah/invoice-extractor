"""Data models for extracted invoices."""
from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class LineItem(BaseModel):
    description: str
    quantity: Decimal = Field(ge=0)
    unit_price: Decimal = Field(ge=0)
    amount: Decimal = Field(ge=0)


class Invoice(BaseModel):
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    vendor_name: Optional[str] = None
    bill_to: Optional[str] = None
    currency: Optional[str] = None
    line_items: List[LineItem] = Field(default_factory=list)
    subtotal: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    total: Optional[Decimal] = None


class ExtractionResult(BaseModel):
    invoice: Invoice
    method: str = Field(description="'rules' or 'llm'")
    warnings: List[str] = Field(default_factory=list)
    needs_review: bool = Field(
        description="True when required fields are missing or the numbers do not add up"
    )
