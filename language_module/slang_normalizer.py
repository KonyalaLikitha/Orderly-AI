"""
slang_normalizer.py
Normalizes regional slang and informal retail speech into clean English.
"""
import re
from deep_translator import GoogleTranslator

# Filler/address words common in retail speech across all supported languages
_FILLER_PREFIXES = ["anna", "bhai", "bhaiya", "didi", "sir", "madam", "boss", "yaar", "re"]

# Transliterated action words that signal untranslated mixed-language text
# These are stripped BEFORE translation so the translator gets cleaner input
_MIXED_ACTION_WORDS = [
    "add cheyyi", "add cheyyandi", "add karo", "add kar",
    "cheyyi", "cheyyandi", "daalo", "daal do", "daal",
    "karo", "karna", "lagao", "hatao", "nikalo", "jodo", "jodna"
]

def _strip_filler_prefix(text: str) -> str:
    words = text.strip().split()
    if words and words[0].lower() in _FILLER_PREFIXES:
        return " ".join(words[1:])
    return text

def _strip_mixed_action_words(text: str) -> str:
    """Remove transliterated action words so translator gets clean item+quantity text."""
    lower = text.lower()
    # Sort by length descending to match multi-word phrases first
    for word in sorted(_MIXED_ACTION_WORDS, key=len, reverse=True):
        lower = re.sub(rf"\b{re.escape(word)}\b", "", lower)
    return re.sub(r"\s{2,}", " ", lower).strip(" .,")

def _has_mixed_signals(text: str) -> bool:
    lower = text.lower()
    return any(word in lower for word in _MIXED_ACTION_WORDS)

def normalize_text(text: str, src_lang: str = "auto") -> str:
    """
    Normalize informal/slang retail speech to clean English.
    Steps:
      1. Strip filler address words (anna, bhai, etc.)
      2. If mixed-language action words detected, strip them and prepend 'add'
         so the translator receives clean item+quantity text.
      3. Translate to English.
    Returns clean English text ready for order parsing.
    """
    text = _strip_filler_prefix(text)

    if _has_mixed_signals(text):
        # Strip the mixed action words, then prepend "add" as the intent
        clean = _strip_mixed_action_words(text)
        text = "add " + clean
        src_lang = "en"  # now it's clean English, no need to auto-detect

    try:
        normalized = GoogleTranslator(source=src_lang, target="en").translate(text)
        return normalized.strip()
    except Exception:
        return text
