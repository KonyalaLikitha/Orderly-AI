import json
import os
import re

_DICT_PATH = os.path.join(os.path.dirname(__file__), "slang_dictionary.json")

def _load_dictionary() -> dict:
    with open(_DICT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize_slang(text: str) -> str:
    dictionary = _load_dictionary()
    # Sort by length descending to match longer phrases first
    for slang, standard in sorted(dictionary.items(), key=lambda x: len(x[0]), reverse=True):
        text = re.sub(rf"\b{re.escape(slang)}\b", standard, text, flags=re.IGNORECASE)
    return text
