import sqlite3

from langchain.tools import tool

from src.constants.constants import INVENTORY_DB

@tool
def query_inventory(item_name: str):
    """
    Retrieve the row from the inventory table with the given item_name.
    Returns the row as a dictionary if found, else None.
    """

    conn = sqlite3.connect(INVENTORY_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM inventory WHERE item_name = ?", (item_name,))
    row = cur.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None