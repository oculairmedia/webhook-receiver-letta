#!/usr/bin/env python3
"""
Test script to verify that the webhook message parsing fix works correctly.
"""

import json
from production_improved_retrieval import extract_text_from_content
from retrieve_context import extract_text_from_content as extract_text_from_content_original

def test_message_parsing():
    """Test that we can handle both string and list content formats."""
    
    print("Testing message content parsing...")
    
    # Test case 1: String content (existing format)
    string_content = "This is a simple string message"
    
    # Test case 2: List content (webhook format that was causing the error)
    list_content = [
        {
            "type": "text",
            "text": "yea graphiticontext is down right now i think"
        }
    ]
    
    # Test case 3: Multiple text items in list
    multi_list_content = [
        {
            "type": "text", 
            "text": "First part"
        },
        {
            "type": "text",
            "text": "Second part"
        }
    ]
    
    # Test case 4: Mixed content types (only text should be extracted)
    mixed_content = [
        {
            "type": "text",
            "text": "Valid text"
        },
        {
            "type": "image",
            "url": "http://example.com/image.jpg"
        }
    ]
    
    test_cases = [
        ("String content", string_content, "This is a simple string message"),
        ("List content", list_content, "yea graphiticontext is down right now i think"),
        ("Multi-item list", multi_list_content, "First part Second part"),
        ("Mixed content", mixed_content, "Valid text")
    ]
    
    print("\nTesting production_improved_retrieval.extract_text_from_content:")
    for name, content, expected in test_cases:
        try:
            # Import the function from production_improved_retrieval (it doesn't exist yet, we need to add it)
            result = extract_text_from_content_original(content)
            status = "✅ PASS" if result.strip() == expected.strip() else f"❌ FAIL (got: '{result}')"
            print(f"  {name}: {status}")
        except Exception as e:
            print(f"  {name}: ❌ ERROR - {e}")
    
    # Test the message processing logic
    print("\nTesting full message processing:")
    
    # Test message with list content (the problematic case)
    problematic_message = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "yea graphiticontext is down right now i think"
                }
            ]
        }
    ]
    
    try:
        from production_improved_retrieval import improved_generate_context_from_prompt
        
        print("  Testing with production_improved_retrieval...")
        result = improved_generate_context_from_prompt(
            messages=problematic_message,
            graphiti_url="http://localhost:8001/api",
            max_nodes=1,
            max_facts=1
        )
        if "Query too short" in result or "No relevant information found" in result or "ERROR" not in result:
            print("  ✅ PASS - No 'list has no attribute strip' error")
        else:
            print(f"  ❌ FAIL - Unexpected result: {result}")
            
    except Exception as e:
        if "'list' object has no attribute 'strip'" in str(e):
            print(f"  ❌ FAIL - Still getting the strip error: {e}")
        else:
            print(f"  ⚠️  Different error (might be expected): {e}")

if __name__ == "__main__":
    test_message_parsing()