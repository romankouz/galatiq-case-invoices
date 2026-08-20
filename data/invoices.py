import sqlite3
import warnings

from src.model_schemas.output import OutputState

from src.constants.constants import INVOICES_DB

def create_invoices_table():
    """Create a SQLite table named 'invoices' using fields from OutputState."""
    # Map basic python types used in OutputState to SQLite types
    field_type_map = {
        int: "INTEGER",
        float: "REAL",
        str: "TEXT",
        bool: "BOOLEAN"
    }
    # Build the table schema for only fields in OutputState
    field_defs = []
    for field_name, field in OutputState.model_fields.items():
        field_type = field.annotation
        # For typing.Literal, assign as TEXT.
        if getattr(field_type, "__origin__", None) is not None and "Literal" in str(field_type.__origin__):
            sqlite_type = "TEXT"
        elif field_type in field_type_map:
            sqlite_type = field_type_map[field_type]
        else:
            sqlite_type = "TEXT"
        # Pick primary key field: from OutputState definition, use 'invoice_number'
        if field_name == "invoice_number":
            field_defs.append(f"{field_name} TEXT PRIMARY KEY")
        else:
            field_defs.append(f"{field_name} {sqlite_type}")
    schema = ", ".join(field_defs)
    create_sql = f"CREATE TABLE IF NOT EXISTS invoices ({schema})"
    with sqlite3.connect(INVOICES_DB) as conn:
        conn.execute(create_sql)
        conn.commit()

def reset_invoices_table():
    conn = sqlite3.connect(INVOICES_DB)
    try:
        conn.execute("DROP TABLE IF EXISTS invoices")
        conn.commit()
    except sqlite3.OperationalError:
        print("Failed to drop the invoices table.")
    finally:
        conn.close()
   

def insert_invoice_to_db(invoice: OutputState):
    """Insert an invoice into the database if it doesn't exist, else raise ValueError."""
    data = invoice.model_dump()
    invoice_number = data.get("invoice_number")
    if invoice_number is None:
        raise ValueError("Invoice missing required field 'invoice_number'; cannot store in DB.")
    with sqlite3.connect(INVOICES_DB) as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM invoices WHERE invoice_number = ?", (invoice_number,))
        if cur.fetchone():
            warnings.warn(f"Invoice '{invoice_number}' already exists in the database. Skipping this invoice.")
            raise ValueError(f"Invoice '{invoice_number}' already exists in the database. Cannot process it again.")
        # Ensure serialization for any non-primitive types if present
        insert_fields = []
        insert_values = []
        for k, v in data.items():
            # All OutputState fields should be primitives (str, float, etc.), safe to insert directly.
            insert_fields.append(k)
            insert_values.append(v)
        columns = ", ".join(insert_fields)
        placeholders = ", ".join(["?"] * len(insert_fields))
        insert_sql = f"INSERT INTO invoices ({columns}) VALUES ({placeholders})"
        cur.execute(insert_sql, insert_values)
        conn.commit()