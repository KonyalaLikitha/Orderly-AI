"""
order_parser.py
Parses bulk retail orders from normalized English text.
Extracts items and quantities using pattern matching — no hardcoded item names.
Works on any item the user mentions.
"""
import re

# Matches patterns like: "50 biscuit packets", "20 bottles of water", "5 kg rice"
_QUANTITY_PATTERN = re.compile(
    r"(\d+)\s*"                          # quantity number
    r"(kg|g|gm|litre|liter|l|dozen|pcs|pieces|units|packets?|packs?|boxes?|bags?|bottles?|cans?|jars?|rolls?|strips?|bundles?)?\s*"  # optional unit
    r"(?:of\s+)?"                        # optional "of"
    r"([a-zA-Z][a-zA-Z\s]{1,30}?)(?=\s*(?:and|,|\.|$|\d))",  # item name
    re.IGNORECASE
)

# Action words to detect intent
_ADD_WORDS    = {"add", "include", "put", "place", "insert", "want", "need", "get", "order"}
_REMOVE_WORDS = {"remove", "delete", "cancel", "take out", "drop", "exclude"}

def _detect_action(text: str) -> str:
    lower = text.lower()
    for word in _REMOVE_WORDS:
        if word in lower:
            return "remove"
    for word in _ADD_WORDS:
        if word in lower:
            return "add"
    return "add"  # default intent for retail orders

def parse_bulk_order(normalized_english: str) -> dict:
    """
    Parse a normalized English order string into structured data.
    Returns:
        {
            "action": "add" | "remove",
            "items": [{"quantity": 50, "unit": "packets", "item": "biscuits"}, ...]
        }
    """
    action = _detect_action(normalized_english)
    items = []

    for match in _QUANTITY_PATTERN.finditer(normalized_english):
        qty_str, unit, item_name = match.groups()
        item_name = item_name.strip()  # keep item name as-is
        entry = {
            "quantity": int(qty_str),
            "unit": unit.lower() if unit else "units",
            "item": item_name.lower()
        }
        items.append(entry)

    return {"action": action, "items": items}
