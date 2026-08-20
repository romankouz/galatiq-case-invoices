"""
Run one uploaded invoice through the same steps as main.py.

This file only *uses* the existing pipeline. It does not change main.py.
Saving to the database is left to the dashboard, so the user can choose when to store a record.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from data.inventory import create_inventory_table, reset_inventory_table
from data.invoices import create_invoices_table, insert_invoice_to_db, reset_invoices_table
from data.table_utils import table_exists
from main import build_agent_graph, mock_payment, mock_rejection
from src.model_schemas.output import OutputState

from errors import UserFacingError


@dataclass
class ProcessResult:
    """The fields the dashboard shows after a file finishes."""

    invoice_number: str
    vendor_name: str
    amount: float
    processing_result: str
    processing_result_sublabel: str
    reason: str
    confidence: float
    payment_action: str


def ensure_tables() -> None:
    """Create the inventory and invoices tables if they are missing — same as main()."""
    if not table_exists("inventory"):
        reset_inventory_table()
        create_inventory_table()

    if not table_exists("invoices"):
        reset_invoices_table()
        create_invoices_table()


def get_agent():
    """Build the LangGraph agent used in main.py."""
    return build_agent_graph()


def _to_output_state(result: ProcessResult) -> OutputState:
    """Rebuild the official OutputState so we can save it later."""
    return OutputState(
        invoice_number=result.invoice_number,
        vendor_name=result.vendor_name,
        amount=result.amount,
        processing_result=result.processing_result,
        processing_result_sublabel=result.processing_result_sublabel,
        reason=result.reason,
        confidence=result.confidence,
    )


def save_result_to_database(result: ProcessResult) -> None:
    """
    Store the processed invoice when the user asks.

    If that invoice number is already stored, raise a plain-language error
    asking for a different Invoice ID.
    """
    ensure_tables()
    invoice = _to_output_state(result)
    try:
        insert_invoice_to_db(invoice)
    except ValueError as exc:
        message = str(exc).lower()
        if "already exists" in message:
            raise UserFacingError(
                f"Invoice {result.invoice_number} is already in Acme's database. "
                "This invoice number needs a different ID before it can be saved properly."
            ) from exc
        raise UserFacingError(
            "Acme could not save this invoice. Please check the record and try again."
        ) from exc


def process_invoice_file(file_path: str, agent=None) -> ProcessResult:
    """
    Follow the single-invoice path in main(), except we do not write to the
    database until the user clicks Upload To Database.

    1. Make sure database tables exist
    2. Run the agent on the file
    3. Turn the result into OutputState
    4. Record a mock payment or rejection
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(file_path)

    ensure_tables()

    if agent is None:
        agent = get_agent()

    processed_invoice = agent.invoke({"file_path": file_path})

    try:
        invoice = OutputState(**processed_invoice)
    except Exception as exc:
        raise UserFacingError(
            "Acme processed the file, but the result was incomplete. Please try another invoice."
        ) from exc

    if invoice.processing_result == "SUCCESS":
        mock_payment(invoice.vendor_name, invoice.amount)
        payment_action = "paid"
    else:
        mock_rejection(invoice.vendor_name, invoice.amount)
        payment_action = "rejected"

    return ProcessResult(
        invoice_number=invoice.invoice_number,
        vendor_name=invoice.vendor_name,
        amount=invoice.amount,
        processing_result=invoice.processing_result,
        processing_result_sublabel=invoice.processing_result_sublabel,
        reason=invoice.reason,
        confidence=invoice.confidence,
        payment_action=payment_action,
    )
