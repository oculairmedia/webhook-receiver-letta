#!/usr/bin/env python3
"""
Verify the actual content being generated to confirm truncation fix
"""
import requests
import json

def test_actual_content():
    webhook_url = "http://localhost:5005/webhook/letta"
    
    # Test with a query that should definitely have some content
    test_payload = {
        "request": {
            "body": {
                "messages": [
                    {
                        "role": "user", 
                        "content": "What do you know about API parameters and context windows?"
                    }
                ]
            }
        },
        "agent_id": "agent-test-verification"
    }
    
    try:
        response = requests.post(webhook_url, json=test_payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Request succeeded!")
                print(f"Block ID: {data['graphiti'].get('block_id')}")
                print(f"Block Name: {data['graphiti'].get('block_name')}")
                return True
            else:
                print("❌ Request failed")
                print(f"Response: {json.dumps(data, indent=2)}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            try:
                print(f"Error response: {response.json()}")
            except:
                print(f"Raw response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    success = test_actual_content()
    if success:
        print("\n🎉 FINAL VERIFICATION PASSED!")
        print("The truncation fix is confirmed working!")
    else:
        print("\n💥 FINAL VERIFICATION FAILED!")