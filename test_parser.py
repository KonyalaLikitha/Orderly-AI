"""
Tests for the Order Parser Module
"""

import sys
sys.path.insert(0, '/workspace/project/Orderly-AI')

from backend.order_parser import parse_transcript, find_product, QUANTITY_WORDS


def test_quantity_words():
    """Test quantity word mapping."""
    assert QUANTITY_WORDS['one'] == 1
    assert QUANTITY_WORDS['two'] == 2
    assert QUANTITY_WORDS['three'] == 3
    print("✓ Quantity words test passed")


def test_parse_single_item():
    """Test parsing single item without quantity."""
    result = parse_transcript("bread")
    assert len(result) == 1
    assert result[0][0] == "Bread"
    assert result[0][1] == 1
    print("✓ Single item test passed")


def test_parse_with_number():
    """Test parsing with digit quantity."""
    result = parse_transcript("5 notebooks")
    assert len(result) == 1
    assert result[0][0] == "Notebook"
    assert result[0][1] == 5
    print("✓ Number quantity test passed")


def test_parse_with_word():
    """Test parsing with word quantity."""
    result = parse_transcript("two milk")
    assert len(result) == 1
    assert result[0][0] == "Milk"
    assert result[0][1] == 2
    print("✓ Word quantity test passed")


def test_fuzzy_matching():
    """Test fuzzy product matching."""
    result = find_product("charger")
    assert result is not None
    assert "Charger" in result['name'] or "charger" in result['name'].lower()
    
    result = find_product("cable")
    assert result is not None
    
    result = find_product("oil")
    assert result is not None
    print("✓ Fuzzy matching test passed")


def test_full_transcripts():
    """Test full transcript parsing."""
    tests = [
        ("one bread", [("Bread", 1)]),
        ("two milk packets", [("Milk", 2)]),
        ("three pen packs", [("Pen Pack", 3)]),
    ]
    
    for transcript, expected in tests:
        result = parse_transcript(transcript)
        assert result == expected, f"Expected {expected}, got {result}"
    
    print("✓ Full transcripts test passed")


if __name__ == "__main__":
    test_quantity_words()
    test_parse_single_item()
    test_parse_with_number()
    test_parse_with_word()
    test_fuzzy_matching()
    test_full_transcripts()
    print("\n✅ All parser tests passed!")
