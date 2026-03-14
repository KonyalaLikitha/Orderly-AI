import re
from language_manager import detect_language
from slang_normalizer import normalize_slang
from translator import translate_to_english, translate_from_english

# Words to strip out — action verbs and filler words
_STRIP_WORDS = r"\b(please|add|remove|cancel|update|put|place|order|cheyyi|karo|do|me|to|my|the|a|an|i|want|need)\b"

_ACTION_REPLIES = {
    "add":    "Sure! I've added {items} to your order.",
    "remove": "Done! I've removed {items} from your order.",
    "cancel": "Your order has been cancelled.",
    "update": "Your order has been updated with {items}.",
}

def _extract_items(translated: str) -> str:
    """Strip action/filler words, return just the item description."""
    cleaned = re.sub(_STRIP_WORDS, "", translated, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" .,")
    return cleaned if cleaned else "your item"

def _build_confirmation(translated: str) -> str:
    lower = translated.lower()
    for action, template in _ACTION_REPLIES.items():
        if action in lower:
            items = _extract_items(lower)
            return template.format(items=items)
    # Fallback: just confirm with extracted items
    items = _extract_items(lower)
    return f"Got it! Your order for {items} has been placed."

def process_voice_command(text: str) -> dict:
    detected_lang = detect_language(text)
    normalized = normalize_slang(text)
    translated = translate_to_english(normalized, src_lang=detected_lang)
    translated_clean = translated.strip().lower()

    confirmation_en = _build_confirmation(translated_clean)
    reply = translate_from_english(confirmation_en, dest_lang=detected_lang)

    return {
        "original": text,
        "detected_language": detected_lang,
        "normalized": normalized,
        "translated": translated_clean,
        "reply": reply
    }
