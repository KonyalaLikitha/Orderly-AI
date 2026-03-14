"""
multilingual_response_generator.py
Generates natural conversational order confirmations.
"""
import re
from deep_translator import GoogleTranslator

def _strip_action_words(text: str) -> str:
    return re.sub(
        r"\b(please|add|remove|delete|cancel|place|put|include|want|need|get|order|cheyyi|cheyyandi|karo|daalo|daal|lagao|yad|cheyyandi)\b",
        "", text, flags=re.IGNORECASE
    ).strip(" .,")

def _build_english_response(action: str, item_desc: str) -> str:
    if action == "remove":
        return f"Sure. I have removed {item_desc} from your order. Would you like to make any other changes?"
    return f"Sure. I have added {item_desc} to your order. Do you want to add anything else?"

def generate_response(parsed_order: dict, target_lang: str, original_text: str = "") -> str:
    action = parsed_order.get("action", "add")

    if target_lang == "en":
        # For English just use parsed items directly
        items = parsed_order.get("items", [])
        parts = []
        for e in items:
            qty, unit, item = e.get("quantity",""), e.get("unit",""), e.get("item","item")
            parts.append(f"{qty} {unit} of {item}" if unit and unit != "units" else f"{qty} {item}")
        item_desc = (" and ".join(parts)) if parts else "your items"
        return _build_english_response(action, item_desc)

    # For non-English: translate original text to English to get natural item names,
    # build the confirmation in English, then translate the whole thing to target language.
    try:
        if original_text:
            en_items = GoogleTranslator(source="auto", target="en").translate(original_text)
            en_items = _strip_action_words(en_items)
        else:
            items = parsed_order.get("items", [])
            parts = []
            for e in items:
                qty, unit, item = e.get("quantity",""), e.get("unit",""), e.get("item","item")
                parts.append(f"{qty} {unit} of {item}" if unit and unit != "units" else f"{qty} {item}")
            en_items = " and ".join(parts) if parts else "your items"

        english_response = _build_english_response(action, en_items)
        return GoogleTranslator(source="en", target=target_lang).translate(english_response)
    except Exception:
        return _build_english_response(action, original_text or "your items")
