#!/usr/bin/env python3
"""
Test the truncation fix in the webhook receiver
"""
import requests
import json

def test_webhook_with_truncation_message():
    """Test webhook with a message that should trigger context retrieval"""
    
    webhook_url = "http://localhost:5005/webhook/letta"
    
    # Create a test payload that should trigger context retrieval
    test_payload = {
        "request": {
            "body": {
                "messages": [
                    {
                        "role": "user",
                        "content": "why would it keep showing --- OLDER ENTRIES TRUNCATED ---"
                    }
                ]
            }
        },
        "agent_id": "agent-1eacfc07-d8b6-4f25-a6ee-aab71934e07a"
    }
    
    try:
        print("Testing truncation fix...")
        print(f"Sending request to: {webhook_url}")
        print(f"Payload: {json.dumps(test_payload, indent=2)}")
        
        response = requests.post(
            webhook_url,
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Response JSON: {json.dumps(response_data, indent=2)}")
            
            # Check if we have the graphiti context
            if 'graphiti' in response_data and 'block' in response_data['graphiti']:
                block_value = response_data['graphiti']['block']['value']
                print(f"\nBlock value length: {len(block_value)}")
                print(f"Block value preview (first 500 chars): {block_value[:500]}")
                
                # Check if it's still showing only truncation
                if block_value.strip() == "--- OLDER ENTRIES TRUNCATED ---":
                    print("\n❌ ISSUE: Still showing only truncation message!")
                    return False
                elif "--- OLDER ENTRIES TRUNCATED ---" in block_value and len(block_value.strip()) > 50:
                    print("\n✅ SUCCESS: Truncation working properly with new content!")
                    return True
                else:
                    print(f"\n✅ SUCCESS: New context generated without truncation issue!")
                    return True
            else:
                print("\n❌ No graphiti block found in response")
                return False
        else:
            print(f"\n❌ Request failed with status {response.status_code}")
            print(f"Response text: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_webhook_with_truncation_message()
    if success:
        print("\n🎉 Truncation fix test PASSED!")
    else:
        print("\n💥 Truncation fix test FAILED!")