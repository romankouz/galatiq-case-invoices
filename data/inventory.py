import sqlite3

from src.constants.constants import INVENTORY_DB, INVOICES_DB

def create_inventory_table():

    conn = sqlite3.connect(INVENTORY_DB)  # Persist to file so all agents can access it
    cursor = conn.cursor()

    cursor.execute('CREATE TABLE IF NOT EXISTS inventory (item_name TEXT PRIMARY KEY, stock INTEGER)')
    cursor.execute("""
        INSERT INTO inventory VALUES
        ('WidgetA', 15),
        ('WidgetB', 10),
        ('GadgetX', 5),
        ('FakeItem', 0)
    """)
    conn.commit()

def reset_inventory_table():
    conn = sqlite3.connect(INVENTORY_DB)
    try:
        conn.execute("DROP TABLE IF EXISTS inventory")
        conn.commit()
    except sqlite3.OperationalError:
        print("Failed to drop the inventory table.")
    finally:
        conn.close()