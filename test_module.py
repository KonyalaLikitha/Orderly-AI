import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

from processor import process_voice_command

TEST_CASES = [
    "Add two milk packets",
    "दो दूध के पैकेट जोड़ो",
    "2 paalu packets add cheyyi"
]

def run_tests():
    print("=" * 55)
    print("  AI Voice Order Management - Language Module Test")
    print("=" * 55)
    for cmd in TEST_CASES:
        print(f"\nInput    : {cmd}")
        result = process_voice_command(cmd)
        print(f"Language : {result['detected_language']}")
        print(f"Normalized: {result['normalized']}")
        print(f"Translated: {result['translated']}")
        print(f"Reply    : {result['reply']}")
        print("-" * 55)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
        result = process_voice_command(user_input)
        print(result)
    else:
        run_tests()
