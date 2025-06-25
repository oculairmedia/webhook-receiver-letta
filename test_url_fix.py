#!/usr/bin/env python3
"""
Test script to verify the URL construction fix
"""

import requests
import json
import time

def test_webhook():
    """Test the webhook to see if URL construction is working"""
    
    # Wait a moment for the server to fully start
    time.sleep(2)
    
    test_payload = {
        "request": {
            "body": {
                "messages": [
                    {
                        "role": "user",
                        "content": "test message"
                    }
                ]
            }
        },
        "webhook_url": "http://localhost:5005/webhook/letta"
    }
    
    try:
        print("Testing webhook URL construction fix...")
        response = requests.post(
            "http://localhost:5005/webhook/letta",
            json=test_payload,
            timeout=10
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            print("✓ Webhook responded successfully")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"✗ Webhook returned error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
    except Exception as e:
        print(f"✗ Test failed: {e}")

if __name__ == "__main__":
    test_webhook()