import sqlite3
import re
from difflib import SequenceMatcher

from langchain.tools import tool

from src.model_schemas.invoice import InvoiceState
from src.constants.constants import INVENTORY_DB

@tool
def calculate_total(invoice: InvoiceState) -> float | None:
    """
    Calculate the total of the invoice. Returns None if the total cannot be calculated.
    """
    if invoice.tax_amount is None:
        invoice.tax_amount = 0
    if invoice.shipping is None:
        invoice.shipping = 0
    if invoice.subtotal is None:
        # Calculate subtotal from line_items. If item.amount is present, use it, else fall back to (quantity * unit_price), else 0.
        if invoice.line_items:
            invoice.subtotal = sum(
                item.amount if item.amount is not None
                else (item.quantity or 0) * (item.unit_price or 0) if item.quantity is not None and item.unit_price is not None
                else 0
                for item in invoice.line_items
            )
        else:
            return None
 
    return invoice.subtotal + invoice.tax_amount + invoice.shipping

@tool
def verify_total(invoice: InvoiceState) -> bool:
    """
    Verify the total of the invoice is correct.
    """
    if invoice.tax_amount is None:
        invoice.tax_amount = 0
    if invoice.shipping is None:
        invoice.shipping = 0
    if invoice.subtotal is not None and invoice.total is not None:
        return abs(invoice.total - (invoice.subtotal + invoice.tax_amount + invoice.shipping)) < 0.01
    if invoice.subtotal is None and invoice.line_items:
        # Recover total from line items by using amount if present, else (quantity * unit_price), else 0
        recovered_total = sum(
            item.amount if item.amount is not None
            else (item.quantity or 0) * (item.unit_price or 0) if item.quantity is not None and item.unit_price is not None
            else 0
            for item in invoice.line_items
        )
        return abs((invoice.total or 0) - recovered_total) < 0.01
    return False

@tool
def verify_tax_calculation(invoice: InvoiceState) -> bool:
    """
    Verify the tax calculation is correct.
    """
    if invoice.tax_rate is None:
        return True
    return abs(invoice.tax_amount - (invoice.subtotal * invoice.tax_rate)) < 0.01

@tool
def verify_quantities(invoice: InvoiceState) -> dict:
    """
    Verify if requested quantities do not exceed available inventory, using normalization and fuzzy matching.
    Returns a dict with pass/fail and candidate inventory item matches.
    """
    # Fetch inventory into a dictionary: {item_name: quantity_available}
    conn = sqlite3.connect(INVENTORY_DB)
    cur = conn.cursor()
    cur.execute("SELECT item_name, stock FROM inventory")
    inventory_db = {row[0]: row[1] for row in cur.fetchall()}
    conn.close()

    def normalize_name(name):
        if not name:
            return ""
        name = name.lower()
        # Remove anything in parentheses (including text and surrounding space)
        name = re.sub(r'\(.*?\)', '', name)
        name = name.strip()
        # Remove non-word characters and spaces
        name = re.sub(r'[\s\W_]+', '', name)
        return name

    # Canonical inventory with normalization for matching
    processed_inventory_db = {
        normalize_name(inv_name): (inv_name, quantity)
        for inv_name, quantity in inventory_db.items()
    }

    # Calculate total quantities requested per normalized item name
    item_totals = {}
    item_orig_names = {}
    requested_orig_full_names = {}
    if invoice.line_items:
        for item in invoice.line_items:
            if item.item_name is None or item.quantity is None:
                continue
            # For matching: canonicalize by removing parentheticals/spaces/punct, but store original too.
            norm_name = normalize_name(item.item_name)
            item_totals[norm_name] = item_totals.get(norm_name, 0) + item.quantity
            item_orig_names[norm_name] = item.item_name
            requested_orig_full_names[norm_name] = item.item_name

    FUZZY_THRESHOLD = 0.90  # 90% similarity

    results = {
        'all_quantities_valid': True,
        'items': []
    }

    for requested_norm_name, requested_qty in item_totals.items():
        orig_requested = requested_orig_full_names[requested_norm_name]
        # Remove parentheticals for containment logic, but preserve for reporting
        base_requested = re.sub(r'\(.*?\)', '', orig_requested).strip().lower()

        all_candidates = []
        inventory_ok = False

        # First, attempt direct containment match by normalized inventory name in cleaned requested name
        direct_match_found = False
        for inv_norm_name, (inv_real_name, available_qty) in processed_inventory_db.items():
            inv_base = inv_real_name.lower()
            # Check if the inventory item name, as a whole word (perhaps with space), appears in the (parenthetical-removed) request name.
            # Allow for partial/substring match but strengthen by ensuring part boundary, e.g., "widgeta" in "widgeta rush order"
            pattern = re.compile(r'\b' + re.escape(inv_base) + r'\b')
            if (inv_base in base_requested) or (pattern.search(base_requested.replace(' ', ''))):
                # Consider direct match, skip fuzzy logic for this one
                all_candidates.append({
                    'inventory_name': inv_real_name,
                    'available_qty': available_qty,
                    'similarity': 1.0,
                    'matching_type': 'direct_containment'
                })
                top_candidate = all_candidates[0]
                if requested_qty <= available_qty:
                    inventory_ok = True
                matched_inventory_name = inv_real_name
                direct_match_found = True
                break
        # If no direct containment match, revert to fuzzy matching
        if not direct_match_found:
            for inv_norm_name, (inv_real_name, available_qty) in processed_inventory_db.items():
                score = SequenceMatcher(None, requested_norm_name, inv_norm_name).ratio()
                if score >= FUZZY_THRESHOLD:
                    all_candidates.append({'inventory_name': inv_real_name, 'available_qty': available_qty, 'similarity': round(score, 3), 'matching_type': 'fuzzy'})
            all_candidates = sorted(all_candidates, key=lambda x: x['similarity'], reverse=True)
            if all_candidates:
                top_candidate = all_candidates[0]
                if requested_qty <= top_candidate['available_qty']:
                    inventory_ok = True
                matched_inventory_name = top_candidate['inventory_name']
            else:
                inventory_ok = False
                matched_inventory_name = None

        if not inventory_ok:
            results['all_quantities_valid'] = False

        results['items'].append({
            'requested_item': item_orig_names[requested_norm_name],
            'requested_qty': requested_qty,
            'candidate_inventory_matches': all_candidates,
            'quantity_valid': inventory_ok
        })

    return results