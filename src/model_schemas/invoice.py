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
        revision: The revision number of the invoice. If the revision number is not naturally provided, please add it.
        vendor: The vendor name of the invoice.
        vendor_address: The vendor address of the invoice.
        bill_to: The bill to address of the invoice.
        date: The date of the invoice.
        due_date: The due date of the invoice.
        line_items: The line items of the invoice.
        subtotal: The subtotal of the invoice.
        tax_rate: The tax rate of the invoice. Should be the decimal, not the percentage.
        tax_amount: The nominal tax amount of the invoice.
        shipping: The nominal shipping amount of the invoice.
        total: The nominal total of the invoice.
        currency: The currency of the invoice.
        payment_terms: The payment terms of the invoice.
        notes: The notes of the invoice.
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