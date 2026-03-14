# Language Processing Module
## AI-Driven Voice Activated Intelligent Order Management System

A fully independent, modular language processing pipeline supporting multilingual input,
regional dialect detection, and slang normalization.

---

## Installation

```bash
pip install langdetect
pip install deep-translator
pip install flask
```

> **Note:** `googletrans==4.0.0-rc1` is incompatible with Python 3.13+ (missing `cgi` module).
> This module uses `deep-translator` instead, which is actively maintained and works on all Python versions.

---

## Folder Structure

```
multilanguage/
├── language_manager.py     # Language detection (langdetect)
├── translator.py           # Translation to/from English (googletrans)
├── slang_normalizer.py     # Slang normalization from JSON dictionary
├── processor.py            # Main pipeline: detect → normalize → translate → reply
├── slang_dictionary.json   # Slang-to-standard word mappings (editable)
├── test_module.py          # CLI test runner
├── app.py                  # Flask backend for UI
├── static/
│   └── index.html          # Web UI
└── README.md
```

---

## Running the CLI Tests

```bash
cd multilanguage
python test_module.py
```

Custom input:
```bash
python test_module.py 2 paalu packets add cheyyi
```

---

## Running the Web UI

```bash
cd multilanguage
python app.py
```

Then open: [http://localhost:5000](http://localhost:5000)

---

## Supported Languages

| Code | Language |
|------|----------|
| `en` | English  |
| `hi` | Hindi    |
| `te` | Telugu   |

---

## Pipeline

```
Voice Input
    ↓
detect_language(text)        → language_manager.py
    ↓
normalize_slang(text)        → slang_normalizer.py  (uses slang_dictionary.json)
    ↓
translate_to_english(text)   → translator.py
    ↓
translate_from_english(reply, lang)  → reply in user's language
    ↓
Structured Output Dict
```

---

## Integration Example

```python
from processor import process_voice_command

result = process_voice_command(transcript)
order_parser(result["translated"])
```

### Output Structure

```json
{
  "original": "2 paalu packets add cheyyi",
  "detected_language": "te",
  "normalized": "2 milk packets add",
  "translated": "add 2 milk packets",
  "reply": "ఆర్డర్ స్వీకరించబడింది: add 2 milk packets"
}
```

---

## Extending Slang Dictionary

Edit `slang_dictionary.json` to add new slang terms — no Python changes needed:

```json
{
  "paalu": "milk",
  "your_slang": "standard_word"
}
```

---

## Test Cases

| Input | Language | Output |
|-------|----------|--------|
| `Add two milk packets` | English | `add two milk packets` |
| `दो दूध के पैकेट जोड़ो` | Hindi | `add two milk packets` |
| `2 paalu packets add cheyyi` | Telugu | `add 2 milk packets` |
