from deep_translator import GoogleTranslator

def translate_to_english(text: str, src_lang: str = "auto") -> str:
    try:
        return GoogleTranslator(source=src_lang, target="en").translate(text)
    except Exception:
        return text

def translate_from_english(text: str, dest_lang: str) -> str:
    if dest_lang == "en":
        return text
    try:
        return GoogleTranslator(source="en", target=dest_lang).translate(text)
    except Exception:
        return text
