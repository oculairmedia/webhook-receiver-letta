#!/usr/bin/env python3
"""
Test script to verify that the extract_text_from_content fix works correctly
for both string and list content formats.
"""

# Test the import and function
try:
    from production_improved_retrieval import extract_text_from_content
    print("✅ Successfully imported extract_text_from_content from production_improved_retrieval")
except ImportError:
    try:
        from retrieve_context import extract_text_from_content
        print("✅ Successfully imported extract_text_from_content from retrieve_context")
    except ImportError:
        print("❌ Failed to import extract_text_from_content from either module")
        exit(1)

# Test cases
test_cases = [
    # String content (should work as before)
    {
        "input": "what about the news in lithuania",
        "description": "Simple string content",
        "expected": "what about the news in lithuania"
    },
    
    # List content (the problematic case we're fixing)
    {
        "input": [{"type": "text", "text": "what about the news in lithuania"}],
        "description": "List content with single text item",
        "expected": "what about the news in lithuania"
    },
    
    # Multiple text items in list
    {
        "input": [
            {"type": "text", "text": "what about"},
            {"type": "text", "text": "the news in lithuania"}
        ],
        "description": "List content with multiple text items",
        "expected": "what about the news in lithuania"
    },
    
    # Mixed content types (should ignore non-text)
    {
        "input": [
            {"type": "text", "text": "what about"},
            {"type": "image", "url": "http://example.com/image.jpg"},
            {"type": "text", "text": "the news in lithuania"}
        ],
        "description": "List content with mixed types",
        "expected": "what about the news in lithuania"
    },
    
    # Empty content
    {
        "input": "",
        "description": "Empty string",
        "expected": ""
    },
    
    # Empty list
    {
        "input": [],
        "description": "Empty list",
        "expected": ""
    }
]

print("\n🧪 Testing extract_text_from_content function:")
print("=" * 50)

all_passed = True

for i, test_case in enumerate(test_cases, 1):
    try:
        result = extract_text_from_content(test_case["input"])
        expected = test_case["expected"]
        
        if result == expected:
            print(f"✅ Test {i}: {test_case['description']}")
            print(f"   Input: {test_case['input']}")
            print(f"   Result: '{result}'")
        else:
            print(f"❌ Test {i}: {test_case['description']}")
            print(f"   Input: {test_case['input']}")
            print(f"   Expected: '{expected}'")
            print(f"   Got: '{result}'")
            all_passed = False
    except Exception as e:
        print(f"❌ Test {i}: {test_case['description']} - Exception: {e}")
        all_passed = False
    
    print()

if all_passed:
    print("🎉 All tests passed! The extract_text_from_content fix is working correctly.")
    print("\n📋 Summary of the fix:")
    print("• Added extract_text_from_content to imports in flask_webhook_receiver.py")
    print("• Modified line ~877: original_prompt_for_logging = extract_text_from_content(content_data)")
    print("• Modified line ~896: original_prompt_for_logging = extract_text_from_content(direct_prompt)")
    print("• This ensures original_prompt_for_logging contains plain text for GDELT keyword matching")
else:
    print("❌ Some tests failed. Please check the implementation.")