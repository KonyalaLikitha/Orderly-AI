"""
Order Parser Module
Parses voice/text orders and extracts product names and quantities.
"""

import json
import os

# Quantity word mapping
QUANTITY_WORDS = {
    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    'a': 1, 'an': 1
}

# Action words
ACTION_WORDS = ['add', 'get', 'buy', 'purchase', 'remove', 'delete', 'clear', 'update']


def load_products():
    """Load products from JSON file."""
    products_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'products.json')
    with open(products_file, 'r') as f:
        data = json.load(f)
    return data['products']


def normalize_text(text):
    """Normalize text for comparison."""
    return text.lower().strip()


def parse_transcript(transcript):
    """
    Parse a transcript to extract product and quantity.
    
    Returns list of tuples: [(product_name, quantity), ...]
    Supports:
    - "one bread" -> [('Bread', 1)]
    - "two milk packets" -> [('Milk', 2)]
    - "5 notebooks" -> [('Notebook', 5)]
    """
    transcript = normalize_text(transcript)
    words = transcript.split()
    
    # Default values
    quantity = 1
    remaining_text = transcript
    
    # Check if first word is a quantity
    if words and words[0] in QUANTITY_WORDS:
        quantity = QUANTITY_WORDS[words[0]]
        remaining_text = ' '.join(words[1:])
    elif words and words[0].isdigit():
        quantity = int(words[0])
        remaining_text = ' '.join(words[1:])
    
    # Find product match
    product = find_product(remaining_text)
    
    if product:
        return [(product['name'], quantity)]
    
    return []


def find_product(transcript):
    """
    Find product using fuzzy/substring matching.
    Matches product name in transcript OR transcript in product name.
    """
    products = load_products()
    transcript = normalize_text(transcript)
    
    # Try exact match first
    for product in products:
        if transcript == product['name'].lower():
            return product
    
    # Try substring matching
    for product in products:
        # Check if product name is in transcript
        if product['name'].lower() in transcript:
            return product
        # Check if transcript is in product name
        if transcript in product['name'].lower():
            return product
        # Check aliases
        for alias in product.get('aliases', []):
            if alias in transcript or transcript in alias:
                return product
    
    # No match found
    return None


def get_product_price(product_name):
    """Get product price by name."""
    products = load_products()
    for product in products:
        if product['name'].lower() == product_name.lower():
            return product['price']
    return None


if __name__ == '__main__':
    # Test cases
    test_cases = [
        "one bread",
        "two milk packets",
        "three pen packs",
        "5 notebooks",
        "charger",
        "cable"
    ]
    
    print("Testing order parser:")
    for test in test_cases:
        result = parse_transcript(test)
        print(f"  '{test}' -> {result}")
