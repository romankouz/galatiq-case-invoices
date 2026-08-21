import zipfile
import os
from typing import Optional, List, Any, Union
import json
import pandas as pd
import xml.etree.ElementTree as ET
import yaml

from markitdown import MarkItDown

from pydantic_core._pydantic_core import ValidationError

from src.model_schemas.input import InputState
from src.model_schemas.invoice import InvoiceState, LineItemState

class FileTypeError(Exception):
    pass

class MissingHeadersError(Exception):
    pass

ALLOWED_EXTENSIONS = [
    '.zip', '.pdf', '.json', '.jsonl', '.doc',
    '.docx', '.xlsx', '.xls', '.xml', '.csv',
    '.tsv', '.txt', '.yaml', '.yml', '.md'
]

def _get_extension(filename):
    return os.path.splitext(filename)[1].lower()

def _read_text(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return {"temp_unstructured_text": content}

def _extract_document_text(file_path: str) -> dict:
    """
    Extract unstructured text from supported document types and return as a dict.
    Uses MarkItDown to extract from .pdf, .doc, .docx (and future document types).
    Falls back to reading as text for other file types.
    """
    # Use MarkItDown for office/docs/pdf types
    md = MarkItDown()
    try:
        result = md.convert(file_path)
        content = result.text_content
    except RuntimeError as e:
        raise FileTypeError(f'Failed to extract {file_path} using MarkItDown: {e}') from e
    return {"temp_unstructured_text": content}

def _read_dict(file_path: str, ext: str):
    if ext == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    if ext == ".jsonl":
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]
        if len(lines) == 0:
            return {}
        elif len(lines) == 1:
            return lines[0]
        else:
            return lines

    if ext in [".yaml", ".yml"]:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    if ext == ".xml":
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ET.parse(f)
            root = tree.getroot()
        return _xml_to_dict(root)
    raise FileTypeError(f"Unsupported dict filetype: {ext}")

def _read_table(file_path: str, ext: str) -> list[dict]:
    if ext in [".csv", ".tsv"]:
        delimiter = "," if ext == ".csv" else "\t"
        df = pd.read_csv(
            file_path,
            delimiter=delimiter,
            dtype=str,
            keep_default_na=False
        )

    elif ext in [".xlsx", ".xls"]:
        df = pd.read_excel(
            file_path,
            dtype=str,
            keep_default_na=False
        )

    else:
        raise FileTypeError(f"Unsupported table filetype: {ext}")

    if any(
        col is None
        or str(col).strip() == ""
        or str(col).startswith("Unnamed:")
        for col in df.columns
    ):
        raise MissingHeadersError(
            f"Table must have non-empty column names: {file_path}"
        )

    return df.to_dict(orient="records")

def _is_tall_table(rows: list[dict]) -> bool:
    if not rows:
        return False

    columns = {str(col).lower() for col in rows[0].keys()}

    return columns == {"field", "value"}

def _tall_table_to_invoice_state(rows: list[dict]) -> Union[InvoiceState, dict]:
    invoice_data = {}
    line_items = []

    current_item = None

    item_fields = {
        "item_name",
        "item",
        "quantity",
        "qty",
        "unit_price",
        "amount",
        "line_total",
        "note",
    }

    for row in rows:
        field = str(row.get("field", "")).strip()
        value = row.get("value")

        normalized_field = field.lower().replace(" ", "_")

        # New item begins
        if normalized_field in {"item_name", "item"}:
            if current_item:
                line_items.append(current_item)

            current_item = {
                "item_name": value
            }

        # We're currently constructing a line item
        elif normalized_field in item_fields and current_item is not None:
            current_item[normalized_field] = value

        # Otherwise it's an invoice-level field
        else:
            invoice_data[normalized_field] = value

    # Don't forget final item
    if current_item:
        line_items.append(current_item)

    if line_items:
        invoice_data["line_items"] = line_items

    return _populate_invoice_from_dict(invoice_data)

def _wide_table_to_invoice_state(
    rows: list[dict]
) -> Union[InvoiceState, dict]:

    if not rows:
        return InvoiceState()

    r0 = rows[0]

    fieldmap = {
        "invoice_number": ["invoice_number", "Invoice Number", "number"],
        "vendor": ["vendor", "Vendor"],
        "date": ["date", "Date"],
        "due_date": ["due_date", "Due Date"],
        "subtotal": ["subtotal", "Subtotal"],
        "tax_amount": ["tax", "Tax", "tax_amount"],
        "total": ["total", "Total"],
        "payment_terms": ["payment_terms", "Payment Terms"],
    }

    invoice_kwargs = {}

    for field, aliases in fieldmap.items():
        invoice_kwargs[field] = next(
            (r0[a] for a in aliases if a in r0),
            None
        )

    item_fields = ["item_name", "item", "Item Name", "Item"]
    quantity_fields = ["quantity", "qty", "Quantity", "Qty"]
    price_fields = ["unit_price", "Unit Price", "unit price"]
    amount_fields = ["amount", "Amount", "line_total", "Line Total"]

    def find_value(row, aliases):
        return next(
            (row[a] for a in aliases if a in row),
            None
        )

    line_items = []

    for row in rows:
        item_name = find_value(row, item_fields)

        if not item_name:
            continue

        line_items.append(
            LineItemState(
                item_name=item_name,
                quantity=_try_int(find_value(row, quantity_fields)),
                unit_price=_try_float(find_value(row, price_fields)),
                amount=_try_float(find_value(row, amount_fields)),
                note=row.get("note"),
            )
        )

    invoice_kwargs["line_items"] = line_items or None

    # Check required fields BEFORE building InvoiceState
    required_fields = ["invoice_number", "vendor", "total", "line_items"]
    if any(
        invoice_kwargs.get(key) in [None, "", []] for key in required_fields
    ):
        return {"temp_structured_output": invoice_kwargs}

    try:
        return InvoiceState(**invoice_kwargs)
    except ValidationError:
        return {"temp_structured_output": invoice_kwargs}

def _rows_to_invoice_state(
    rows: list[dict],
    ext: Optional[str] = None
) -> Union[InvoiceState, dict]:

    if not rows:
        return InvoiceState()

    if _is_tall_table(rows):
        return _tall_table_to_invoice_state(rows)

    return _wide_table_to_invoice_state(rows)

def _invoice_filled_score(invoice: Union[InvoiceState, dict]) -> int:
    """
    Heuristic: count how many of critical fields could be extracted.
    """
    keys_of_interest = [
        "invoice_number", "vendor", "date", "total",
        "line_items"
    ]
    if isinstance(invoice, dict) and 'temp_structured_output' in invoice:
        d = invoice['temp_structured_output']
        if not isinstance(d, dict):
            return 0
        cnt = sum(bool(d.get(k)) for k in keys_of_interest)
        return cnt
    cnt = 0
    for k in keys_of_interest:
        v = getattr(invoice, k, None)
        if v is not None and v != "" and v != []:
            cnt += 1
    return cnt

def ingest_file(state: InputState) -> Union[dict, InvoiceState]:
    """
    Ingest a file and return the (un)structured output.
    Returns a dictionary if the file is not a supported type, or an InvoiceState object if it is supported.
    """

    ext = _get_extension(state.file_path)
    if ext not in ALLOWED_EXTENSIONS:
        raise FileTypeError(f"Unsupported file type: {ext}")

    if ext in [".txt", ".md"]:
        return _read_text(state.file_path)

    if ext in [".json", ".jsonl", ".yaml", ".yml", ".xml"]:
        data = _read_dict(state.file_path, ext)

        if isinstance(data, list):
            return _rows_to_invoice_state(data)

        return _populate_invoice_from_dict(data)

    if ext in [".csv", ".tsv", ".xlsx", ".xls"]:
        rows = _read_table(state.file_path, ext)
        # Pass ext so CSV/TSV triggers special logic
        return _rows_to_invoice_state(rows, ext)

    if ext in [".pdf", ".doc", ".docx"]:
        return _extract_document_text(state.file_path)

    if ext == ".zip":
        # Unpack zip and attempt to process the first supported file
        with zipfile.ZipFile(state.file_path, "r") as zipf:
            for fname in zipf.namelist():
                if _get_extension(fname) in ALLOWED_EXTENSIONS:
                    with zipf.open(fname) as f:
                        temp_file = f"/tmp/{os.path.basename(fname)}"
                        with open(temp_file, "wb") as out:
                            out.write(f.read())
                        temp_state = InputState(file_path=temp_file)
                        result = ingest_file(temp_state)
                        os.remove(temp_file)
                        return result
        raise FileTypeError("No supported file found inside .zip")


    raise FileTypeError(f"Could not parse file: {state.file_path}")

def _populate_invoice_from_dict(data: dict) -> Union[InvoiceState, dict]:
    if not isinstance(data, dict):
        return InvoiceState()
    # List of required logical keys and their possible aliases
    required_keys_options = {
        "invoice_number": ["invoice_number", "InvoiceNumber", "number"],
        "vendor": ["vendor", "Vendor"],
        "total": ["total", "Total"],
        "line_items": ["line_items", "items"],
    }
    # Check if any required field is missing
    missing_required = False
    for logical_key, options in required_keys_options.items():
        if not any(opt in data and data[opt] not in [None, ""] and data[opt] != [] for opt in options):
            missing_required = True
            break
    if missing_required:
        return {"temp_structured_output": data}

    # Helper to resolve aliases with preference order
    def _resolve(*fieldnames):
        for field in fieldnames:
            v = data.get(field)
            if v is not None:
                return v
        return None

    extracted_fields = {
        "invoice_number": _resolve("invoice_number", "InvoiceNumber", "number"),
        "revision": _resolve("revision", "Revision"),
        "vendor": _resolve("vendor", "Vendor"),
        "vendor_address": _resolve("vendor_address", "VendorAddress"),
        "bill_to": _resolve("bill_to", "BillTo"),
        "date": _resolve("date", "Date"),
        "due_date": _resolve("due_date", "DueDate"),
        "subtotal": _try_float(_resolve("subtotal", "Subtotal")),
        "tax_rate": _try_float(_resolve("tax_rate", "TaxRate")),
        "tax_amount": _try_float(_resolve("tax_amount", "tax", "Tax", "TaxAmount")),
        "shipping": _try_float(_resolve("shipping", "Shipping")),
        "total": _try_float(_resolve("total", "Total")),
        "currency": _resolve("currency", "Currency"),
        "payment_terms": _resolve("payment_terms", "PaymentTerms"),
        "notes": _resolve("notes", "Notes"),
        "line_items": _infer_line_items(data)
    }
    try:
        return InvoiceState(**extracted_fields)
    except ValidationError:
        return {"temp_structured_output": extracted_fields}

def _xml_to_dict(elem) -> dict:
    """
    Recursively converts an XML element tree into a dict, handling repeated tags as lists.
    """
    children = list(elem)
    if children:
        d = {}
        tag_count = {}
        for child in children:
            child_dict = _xml_to_dict(child)
            tag = child.tag

            # Count occurrences of each tag
            tag_count[tag] = tag_count.get(tag, 0) + 1

            if tag not in d:
                d[tag] = child_dict
            else:
                # Convert to list if repeated tag
                if not isinstance(d[tag], list):
                    d[tag] = [d[tag]]
                d[tag].append(child_dict)
        return d
    else:
        return elem.text

def _infer_line_items(
    data: dict
) -> Optional[List[LineItemState]]:

    items = data.get("line_items") or data.get("items")

    # XML commonly produces:
    #
    # {"items": {"item": [{...}, {...}]}}
    #
    if isinstance(items, dict):
        items = (
            items.get("item")
            or items.get("line_item")
            or items.get("LineItem")
        )

    # One XML <item> instead of several
    if isinstance(items, dict):
        items = [items]

    if not isinstance(items, list):
        return None

    line_items = []

    for item in items:
        if not isinstance(item, dict):
            continue

        line_items.append(
            LineItemState(
                item_name=(
                    item.get("item_name")
                    or item.get("item")
                    or item.get("ItemName")
                    or item.get("Item")
                ),
                quantity=_try_int(
                    item.get("quantity")
                    or item.get("Quantity")
                ),
                unit_price=_try_float(
                    item.get("unit_price")
                    or item.get("UnitPrice")
                ),
                amount=_try_float(
                    item.get("amount")
                    or item.get("Amount")
                ),
                note=item.get("note") or item.get("Note"),
            )
        )

    return line_items or None

def _try_float(val: Any) -> Optional[float]:
    try:
        return float(val) if val is not None and val != "" else None
    except (ValueError, TypeError):
        return None

def _try_int(val: Any) -> Optional[int]:
    try:
        return int(val) if val is not None and val != "" else None
    except (ValueError, TypeError):
        return None