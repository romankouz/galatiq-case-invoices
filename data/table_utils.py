import sqlite3
from src.constants.constants import INVENTORY_DB, INVOICES_DB

def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    if table_name == "inventory":
        table = INVENTORY_DB
    elif table_name == "invoices":
        table = INVOICES_DB
    else:
        raise ValueError(f"Table '{table_name}' does not exist.")
    conn = sqlite3.connect(table)
    cursor = conn.cursor()
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    return cursor.fetchone() is not None

def print_all_rows(table_name: str):
    """Print all rows of a table."""
    if table_name == "inventory":
        table = INVENTORY_DB
    elif table_name == "invoices":
        table = INVOICES_DB
    else:
        raise ValueError(f"Table '{table_name}' does not exist.")
    conn = sqlite3.connect(table)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    return cursor.fetchall()