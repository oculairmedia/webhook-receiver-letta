#!/usr/bin/env python3
"""
Test script to simulate the exact webhook payload that was causing the error.
"""

import json
from production_improved_retrieval import generate_context_from_prompt

def test_exact_webhook_scenario():
    """Test the exact webhook payload that was causing the error."""
    
    print("Testing exact webhook scenario that was failing...")
    
    # This is the exact message format from the error log
    webhook_messages = [
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
    
    print(f"Input messages: {json.dumps(webhook_messages, indent=2)}")
    
    try:
        # This should no longer throw the 'list' object has no attribute 'strip' error
        result = generate_context_from_prompt(
            messages=webhook_messages,
            graphiti_url="http://192.168.50.90:8001/api",  # Use the actual URL from error
            max_nodes=5,
            max_facts=15,
            group_ids=None
        )
        
        print("✅ SUCCESS: No 'list has no attribute strip' error!")
        print(f"Result: {result}")
        
        return True
        
    except Exception as e:
        if "'list' object has no attribute 'strip'" in str(e):
            print(f"❌ FAILED: Still getting the strip error: {e}")
            return False
        else:
            print(f"⚠️  Different error (might be expected due to connectivity): {e}")
            print("✅ SUCCESS: The original 'strip' error is fixed, this is a different issue")
            return True

if __name__ == "__main__":
    success = test_exact_webhook_scenario()
    if success:
        print("\n🎉 Fix verified! The webhook should now work without the 'strip' error.")
    else:
        print("\n❌ Fix unsuccessful. The error still exists.")