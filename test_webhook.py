#!/usr/bin/env python3
"""
Simple test script to send a webhook request and diagnose issues
"""

import requests
import json
import sys

def test_webhook(url="http://localhost:5005"):
    """Test the webhook with various payloads"""
    
    print(f"Testing webhook at: {url}")
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{url}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"   Health check failed: {e}")
    
    # Test 2: Debug endpoint (if available)
    print("\n2. Testing debug endpoint...")
    try:
        response = requests.get(f"{url}/debug", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            debug_data = response.json()
            print("   Import Status:")
            for module, status in debug_data.get('imports', {}).items():
                print(f"     {module}: {status}")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Debug check failed: {e}")
    
    # Test 3: Simple webhook with direct prompt
    print("\n3. Testing webhook with simple prompt...")
    simple_payload = {
        "prompt": "test message"
    }
    
    try:
        response = requests.post(
            f"{url}/webhook/letta", 
            json=simple_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Webhook successful!")
            result = response.json()
            print(f"   Context length: {result.get('context_length', 'N/A')}")
        else:
            print(f"   ❌ Webhook failed")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown')}")
                if 'traceback' in error_data:
                    print(f"   Traceback: {error_data['traceback']}")
            except:
                print(f"   Raw response: {response.text}")
                
    except Exception as e:
        print(f"   Webhook test failed: {e}")
    
    # Test 4: Webhook with Letta message format
    print("\n4. Testing webhook with Letta message format...")
    letta_payload = {
        "request": {
            "body": {
                "messages": [
                    {"role": "user", "content": "Hello, this is a test message"}
                ]
            },
            "path": "/v1/agents/agent-test123/messages"
        }
    }
    
    try:
        response = requests.post(
            f"{url}/webhook/letta", 
            json=letta_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Letta format webhook successful!")
            result = response.json()
            print(f"   Context length: {result.get('context_length', 'N/A')}")
        else:
            print(f"   ❌ Letta format webhook failed")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown')}")
                if 'traceback' in error_data:
                    print(f"   Traceback: {error_data['traceback']}")
            except:
                print(f"   Raw response: {response.text}")
                
    except Exception as e:
        print(f"   Letta format webhook test failed: {e}")

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5005"
    test_webhook(url)