#!/usr/bin/env python3
"""
Test the fixed GDELT trigger functionality
"""

import requests
import json

def test_gdelt_trigger():
    """Test that GDELT trigger now works with proper logic"""
    
    print("🧪 TESTING GDELT TRIGGER FIX")
    print("="*50)
    
    # Test webhook URL
    webhook_url = "http://localhost:5000/webhook/letta"
    
    # Test payload with news-related query
    test_payload = {
        "type": "letta_message",
        "letta_message": {
            "message": "What breaking events are happening globally today?",
            "user_id": "test_user",
            "agent_id": "test_agent"
        }
    }
    
    print("📤 Sending test webhook with news query...")
    print(f"Query: '{test_payload['letta_message']['message']}'")
    
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
            
            # Check if GDELT was properly triggered
            if "GDELT" in response.text:
                print("🔍 Checking GDELT trigger in response...")
                # Look for the trigger message
                if "GDELT invocation determined necessary" in response.text:
                    print("✅ GDELT TRIGGER WORKING! Found: 'GDELT invocation determined necessary'")
                elif "GDELT invocation not needed" in response.text:
                    print("❌ GDELT still not triggering - found: 'GDELT invocation not needed'")
                else:
                    print("🔍 GDELT mentioned but trigger status unclear")
            else:
                print("⚠️ No GDELT mention found in response")
                
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to webhook server")
        print("🔧 Make sure the webhook server is running on localhost:5000")
    except Exception as e:
        print(f"❌ Error testing webhook: {e}")
    
    print("\n🔍 MANUAL VERIFICATION:")
    print("Check the webhook server logs for:")
    print("• '[GDELT] GDELT invocation determined necessary for category: ...'")
    print("• Instead of: '[GDELT] GDELT invocation not needed for this query.'")

if __name__ == "__main__":
    test_gdelt_trigger()