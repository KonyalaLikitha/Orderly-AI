"""
language_detector.py
Detects language from voice text.
Supports: English, Hindi, Telugu, Tamil, Marathi.
"""
from langdetect import detect, LangDetectException

SUPPORTED = {
    "en": "English",
    "hi": "Hindi",
    "te": "Telugu",
    "ta": "Tamil",
    "mr": "Marathi",
}

# Unicode script ranges
_SCRIPT_RANGES = {
    "te": (0x0C00, 0x0C7F),
    "ta": (0x0B80, 0x0BFF),
}

# Transliterated regional keywords mapped to their language
# These words are unambiguous markers of a specific language
_TRANSLITERATED_MARKERS = {
    "te": [
        "cheyyi", "cheyyandi", "gantalu", "packetlu", "bottlesu", "bagulu",
        "mariyu", "neellu", "anni", "oka", "rendu", "moodu", "naalu", "aidu",
        "aru", "edu", "enimidi", "tommidi", "padi", "anna", "avunu", "ledu",
        "kilo", "petti", "teeyi", "ivvu", "kavali",
    ],
    "hi": [
        "daalo", "daal", "karo", "karna", "chahiye", "baje", "baara", "gyarah",
        "das", "nau", "aath", "saat", "chhe", "paanch", "char", "teen",
        "bhai", "bhaiya", "yaar", "aur", "ek", "do", "lagao", "hatao",
        "nikalo", "jodo", "dena", "lena", "rakh",
    ],
    "ta": [
        "saerkka", "vendum", "paakettu", "thayavu", "seyya", "oru", "rendu",
    ],
    "mr": [
        "ghya", "taka", "ani", "nako", "dya", "kara",
    ],
}

def _script_detect(text: str) -> str | None:
    for ch in text:
        cp = ord(ch)
        if 0x0C00 <= cp <= 0x0C7F:
            return "te"
        if 0x0B80 <= cp <= 0x0BFF:
            return "ta"
    # Devanagari (Hindi/Marathi)
    if any(0x0900 <= ord(ch) <= 0x097F for ch in text):
        try:
            lang = detect(text)
            return lang if lang in ("hi", "mr") else "hi"
        except LangDetectException:
            return "hi"
    return None

def _transliteration_detect(text: str) -> str | None:
    """Detect language from transliterated regional keywords."""
    lower = text.lower()
    scores = {lang: 0 for lang in _TRANSLITERATED_MARKERS}
    for lang, markers in _TRANSLITERATED_MARKERS.items():
        for word in markers:
            if word in lower:
                scores[lang] += 1
    best_lang = max(scores, key=scores.get)
    return best_lang if scores[best_lang] > 0 else None

def detect_language(text: str) -> str:
    # 1. Script-based (most reliable for native script input)
    script_lang = _script_detect(text)
    if script_lang:
        return script_lang
    # 2. Transliterated keyword matching
    trans_lang = _transliteration_detect(text)
    if trans_lang:
        return trans_lang
    # 3. langdetect fallback
    try:
        lang = detect(text)
        return lang if lang in SUPPORTED else "en"
    except LangDetectException:
        return "en"

def get_language_name(code: str) -> str:
    return SUPPORTED.get(code, code.upper())
