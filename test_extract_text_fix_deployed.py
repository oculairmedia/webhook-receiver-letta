#!/usr/bin/env python3
"""
Test script to verify that the extract_text_from_content fix works correctly
in the deployed flask_webhook_receiver.py file.
"""

import sys

# Test importing the function
try:
    from flask_webhook_receiver import extract_text_from_content
    print("✅ Successfully imported extract_text_from_content from flask_webhook_receiver")
except ImportError as e:
    print(f"❌ Failed to import extract_text_from_content: {e}")
    sys.exit(1)

# Test cases
test_cases = [
    {
        "name": "String content",
        "input": "Hello world",
        "expected": "Hello world"
    },
    {
        "name": "List content with single text item",
        "input": [{"type": "text", "text": "hey there"}],
        "expected": "hey there"
    },
    {
        "name": "List content with multiple text items",
        "input": [
            {"type": "text", "text": "yea i want to know"},
            {"type": "text", "text": "what new discoveries"},
            {"type": "text", "text": "have been made"}
        ],
        "expected": "yea i want to know what new discoveries have been made"
    },
    {
        "name": "Mixed list content (only text items should be extracted)",
        "input": [
            {"type": "text", "text": "Hello"},
            {"type": "image", "url": "http://example.com/image.jpg"},
            {"type": "text", "text": "world"}
        ],
        "expected": "Hello world"
    },
    {
        "name": "Empty list",
        "input": [],
        "expected": ""
    },
    {
        "name": "None/other type",
        "input": None,
        "expected": "None"
    }
]

print("\n🧪 Testing extract_text_from_content function:")
print("=" * 50)

all_passed = True
for i, test_case in enumerate(test_cases, 1):
    print(f"\nTest {i}: {test_case['name']}")
    print(f"Input: {test_case['input']}")
    
    try:
        result = extract_text_from_content(test_case["input"])
        expected = test_case["expected"]
        
        if result == expected:
            print(f"✅ PASS - Output: '{result}'")
        else:
            print(f"❌ FAIL - Expected: '{expected}', Got: '{result}'")
            all_passed = False
    except Exception as e:
        print(f"❌ ERROR - Exception: {e}")
        all_passed = False

print("\n" + "=" * 50)
if all_passed:
    print("🎉 All tests passed! The extract_text_from_content fix is working correctly.")
    print("\n📋 Summary of the fix:")
    print("• Added extract_text_from_content function to the fallback ImportError section")
    print("• This ensures the function is available even when imports fail")
    print("• The deployed webhook should now work correctly")
else:
    print("❌ Some tests failed. Please check the implementation.")