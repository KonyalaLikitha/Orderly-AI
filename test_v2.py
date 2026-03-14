import sys, os
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(__file__))

from language_module.pipeline import process_voice_command

TESTS = [
    ("English",  "Add 50 biscuit packets and 20 water bottles"),
    ("Hindi",    "50 बिस्कुट के पैकेट और 20 पानी की बोतलें जोड़ो"),
    ("Telugu",   "50 బిస్కెట్ ప్యాకెట్లు మరియు 20 నీళ్ల బాటిల్స్ యాడ్ చేయండి"),
    ("Tamil",    "50 பிஸ்கட் பாக்கெட்டும் 20 தண்ணீர் பாட்டிலும் சேர்க்கவும்"),
    ("Marathi",  "50 बिस्किटचे पॅकेट आणि 20 पाण्याच्या बाटल्या जोडा"),
    ("Slang TE", "anna 30 rice bags add cheyyi"),
    ("Slang HI", "bhai 40 soap boxes daalo"),
]

print("=" * 65)
print("  Language Module — Bulk Retail Order Pipeline Test")
print("=" * 65)

for label, cmd in TESTS:
    print(f"\n[{label}]")
    print(f"  Input      : {cmd}")
    r = process_voice_command(cmd)
    print(f"  Detected   : {r['language_name']} ({r['detected_language']})")
    print(f"  Normalized : {r['normalized']}")
    print(f"  Parsed     : {r['parsed_order']}")
    print(f"  Reply      : {r['reply']}")
    print("-" * 65)
