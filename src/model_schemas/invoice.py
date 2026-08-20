from typing import Literal
from pydantic import BaseModel

class LineItemState(BaseModel):
    item_name: str | None = None
    quantity: int | None = None
    unit_price: float | None = None
    amount: float | None = None
    note: str | None = None

class InvoiceState(BaseModel):
    """
        invoice_number: The invoice number usually written with the "INV-" prefix. If the prefix is not naturally provided, please add it.
    """
    invoice_number: str | None = None
    revision: str | None = None
    vendor: str | None = None
    vendor_address: str | None = None
    bill_to: str | None = None
    date: str | None = None
    due_date: str | None = None
    line_items: list[LineItemState] | None = None
    subtotal: float | None = None
    tax_rate: float | None = None
    tax_amount: float | None = None
    shipping: float | None = None
    total: float | None = None
    currency: str | None = None
    payment_terms: str | None = None
    notes: str | None = None