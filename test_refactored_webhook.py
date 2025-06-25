#!/usr/bin/env python3
"""
Test the refactored webhook server with Graphiti integration
"""

import requests
import json
import time

def test_refactored_webhook():
    """Test the refactored webhook to see if Graphiti integration works"""
    
    test_payload = {
        "type": "message_sent",
        "prompt": "test graphiti integration",
        "response": {
            "agent_id": "test-agent-123"
        }
    }
    
    try:
        print("Testing refactored webhook with Graphiti integration...")
        
        response = requests.post(
            "http://localhost:5005/webhook",
            json=test_payload,
            timeout=45
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            print("✓ Refactored webhook responded successfully")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"✗ Webhook returned error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
    except Exception as e:
        print(f"✗ Test failed: {e}")

if __name__ == "__main__":
    # Wait for server to start
    time.sleep(3)
    test_refactored_webhook()