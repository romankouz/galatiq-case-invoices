from src.model_schemas.invoice import InvoiceState
from src.constants.constants import INVENTORY_DB
import sqlite3

from langchain.tools import tool

@tool
def verify_total(invoice: InvoiceState) -> bool:
    """
    Verify the total of the invoice is correct.
    """
    return invoice.total == invoice.subtotal + invoice.tax_amount + invoice.shipping

@tool
def verify_tax_calculation(invoice: InvoiceState) -> bool:
    """
    Verify the tax calculation is correct.
    """
    return invoice.tax_amount == invoice.subtotal * invoice.tax_rate

@tool
def verify_quantities(invoice: InvoiceState) -> bool:
    """
    Verify the quantities of the invoice are correct.
    """
    # Fetch inventory into a dictionary: {item_name: quantity_available}
    conn = sqlite3.connect(INVENTORY_DB)
    cur = conn.cursor()
    cur.execute("SELECT item_name, quantity FROM inventory")
    inventory_db = {row[0]: row[1] for row in cur.fetchall()}
    conn.close()

    item_totals = {}
    if invoice.line_items:
        for item in invoice.line_items:
            if item.item_name is None or item.quantity is None:
                continue
            item_totals[item.item_name] = item_totals.get(item.item_name, 0) + item.quantity

    for item_name, requested_qty in item_totals.items():
        available_qty = inventory_db.get(item_name)
        if available_qty is None or requested_qty > available_qty:
            return False
    return True