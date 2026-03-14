"""
pipeline.py
Main processing pipeline for the language module.
This is the single integration point for other team modules.

Usage:
    from language_module.pipeline import process_voice_command
    result = process_voice_command(transcript)
    order_parser_module(result["parsed_order"])
"""
from .language_detector import detect_language, get_language_name
from .slang_normalizer import normalize_text
from .order_parser import parse_bulk_order
from .multilingual_response_generator import generate_response


def process_voice_command(voice_text: str) -> dict:
    """
    Full pipeline:
      voice_text
        → detect_language()
        → normalize_text()       (slang + dialect → clean English)
        → parse_bulk_order()     (extract items + quantities)
        → generate_response()    (natural reply in user's language)

    Returns:
        {
            "original":          raw voice input,
            "detected_language": language code (en/hi/te/ta/mr),
            "language_name":     human-readable language name,
            "normalized":        clean English text after normalization,
            "parsed_order":      {"action": "add", "items": [...]},
            "reply":             confirmation in user's language
        }
    """
    detected_lang = detect_language(voice_text)
    normalized_en = normalize_text(voice_text, src_lang=detected_lang)
    parsed_order  = parse_bulk_order(normalized_en)
    reply         = generate_response(parsed_order, target_lang=detected_lang, original_text=voice_text)

    return {
        "original":          voice_text,
        "detected_language": detected_lang,
        "language_name":     get_language_name(detected_lang),
        "normalized":        normalized_en,
        "parsed_order":      parsed_order,
        "reply":             reply
    }
