#!/usr/bin/env python3
"""
Test the fixed GDELT trigger functionality with proper payload format
"""

import requests
import json

def test_gdelt_trigger():
    """Test that GDELT trigger now works with proper logic"""
    
    print("🧪 TESTING GDELT TRIGGER FIX")
    print("="*50)
    
    # Test webhook URL
    webhook_url = "http://localhost:5000/webhook/letta"
    
    # Test payload with proper format that includes messages array
    test_payload = {
        "messages": [
            {
                "role": "user",
                "content": "What breaking events are happening globally today?"
            }
        ],
        "prompt": "What breaking events are happening globally today?",
        "agent_id": "test_agent_123",
        "user_id": "test_user_456"
    }
    
    print("📤 Sending test webhook with news query...")
    print(f"Query: '{test_payload['prompt']}'")
    
    try:
        response = requests.post(
            webhook_url,
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Webhook request successful!")
            response_data = response.json()
            print(f"📋 Response: {json.dumps(response_data, indent=2)}")
            
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to webhook server")
        print("🔧 Make sure the webhook server is running on localhost:5000")
    except Exception as e:
        print(f"❌ Error testing webhook: {e}")
    
    print("\n🔍 CHECK WEBHOOK LOGS:")
    print("Look for these messages in the webhook server logs:")
    print("✅ SUCCESS: '[GDELT] GDELT invocation determined necessary for category: global_events'")
    print("❌ FAILURE: '[GDELT] GDELT invocation not needed for this query.'")

if __name__ == "__main__":
    test_gdelt_trigger()