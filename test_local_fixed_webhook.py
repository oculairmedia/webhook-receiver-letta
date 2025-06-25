#!/usr/bin/env python3
"""
Test script to verify the locally running Flask webhook receiver
with the identity resolution fix.
"""

import requests
import json
import time

def test_local_webhook():
    """Test the locally running webhook receiver"""
    print("🧪 TESTING LOCAL WEBHOOK RECEIVER")
    print("=" * 60)
    
    # Test local endpoint
    local_url = "http://localhost:5000/webhook/letta"
    
    # Test payload matching the exact Letta webhook format
    test_payload = {
        "data": [
            {
                "type": "stream_chunk",
                "chunk": {
                    "choices": [
                        {
                            "delta": {
                                "content": "Hello, this is a test message to verify identity resolution works correctly."
                            }
                        }
                    ]
                }
            }
        ],
        "request": {
            "path": "/v1/agents/agent-9c48bb82-46e3-4be6-80eb-8ca43e3a68b6/messages/stream",
            "method": "POST",
            "body": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Test message to verify identity resolution works correctly"
                            }
                        ]
                    }
                ]
            }
        },
        "response": {
            "type": "stream_started",
            "id": "test_msg_123",
            "stream_id": "test_stream_123"
        }
    }
    
    # Extract agent ID from the request path for display
    agent_id = test_payload['request']['path'].split('/')[3]
    
    print(f"📍 Testing endpoint: {local_url}")
    print(f"🔧 Agent ID: {agent_id}")
    print("⏳ Sending test webhook...")
    
    try:
        response = requests.post(
            local_url,
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Webhook processed without errors!")
            
            # Parse response
            try:
                response_data = response.json()
                print("\n🔍 Response Analysis:")
                
                # Check for identity_name in the response
                graphiti_data = response_data.get('graphiti', {})
                if 'identity_name' in graphiti_data:
                    print(f"   👤 Identity Resolution: ✅ SUCCESS - Found identity: {graphiti_data['identity_name']}")
                else:
                    print("   👤 Identity Resolution: ❌ FAILED - No identity_name in response")
                
                # Check other components
                if response_data.get('agent_id'):
                    print(f"   🤖 Agent ID Extraction: ✅ SUCCESS")
                else:
                    print("   🤖 Agent ID Extraction: ❌ FAILED")
                
                if 'graphiti' in response_data:
                    print("   🧠 Graphiti Integration: ✅ SUCCESS")
                else:
                    print("   🧠 Graphiti Integration: ❌ FAILED")
                
                if 'memory_block' in response_data:
                    print("   📝 Memory Block: ✅ SUCCESS")
                else:
                    print("   📝 Memory Block: ❌ FAILED")
                
                # Show full response for debugging
                print(f"\n📄 Full Response:")
                print(json.dumps(response_data, indent=2))
                
            except json.JSONDecodeError:
                print("❌ ERROR: Invalid JSON response")
                print(f"Raw response: {response.text}")
        else:
            print(f"❌ ERROR: Webhook failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to local server")
        print("Make sure the Flask server is running on localhost:5000")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_local_webhook()