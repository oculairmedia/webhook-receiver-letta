#!/usr/bin/env python3
"""
Test the timeout fix to verify it works properly
"""

import requests
import json
import time

def test_webhook_with_timeout_fix():
    """Test the webhook to see if timeout handling is improved"""
    
    test_payload = {
        "request": {
            "body": {
                "messages": [
                    {
                        "role": "user", 
                        "content": "test timeout fix"
                    }
                ]
            }
        },
        "webhook_url": "http://localhost:5005/webhook/letta"
    }
    
    try:
        print("Testing webhook timeout handling fix...")
        print("This test simulates a query that might timeout...")
        
        response = requests.post(
            "http://localhost:5005/webhook/letta",
            json=test_payload,
            timeout=45  # Give more time for the webhook to handle the timeout gracefully
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            print("✓ Webhook responded successfully")
            result = response.json()
            
            # Check if the response contains timeout error handling
            graphiti_response = result.get("graphiti", {})
            if "timeout" in str(graphiti_response).lower() or "error" in str(graphiti_response).lower():
                print("ℹ️  Timeout was handled gracefully by the webhook")
            else:
                print("✓ No timeout occurred - Graphiti responded normally")
                
            print(f"Response summary: {result.get('message', 'No message')}")
        else:
            print(f"✗ Webhook returned error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("✗ Test itself timed out - webhook may still be processing")
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
    except Exception as e:
        print(f"✗ Test failed: {e}")

if __name__ == "__main__":
    test_webhook_with_timeout_fix()