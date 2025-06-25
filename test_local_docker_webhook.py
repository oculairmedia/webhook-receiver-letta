#!/usr/bin/env python3
"""
Test script to send a webhook request to the locally running Docker container
to verify the extract_text_from_content and tool functions are working.
"""

import requests
import json

# Test webhook payload (similar to what Letta sends)
test_payload = {
    "type": "stream_started",
    "timestamp": "2025-06-07T18:44:30.000Z",
    "prompt": [
        {
            "type": "text",
            "text": "test webhook with fixed functions"
        }
    ],
    "request": {
        "path": "/v1/agents/agent-1eacfc07-d8b6-4f25-a6ee-aab71934e07a/messages/stream",
        "method": "POST",
        "body": {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "test webhook with fixed functions"
                        }
                    ]
                }
            ]
        }
    },
    "response": {
        "type": "stream_started",
        "timestamp": "2025-06-07T18:44:30.000Z"
    }
}

# Send the webhook request to the Docker container
url = "http://localhost:5005/webhook"
headers = {
    "Content-Type": "application/json",
    "X-Webhook-Secret": "test-secret-key"
}

print("🧪 Testing local Docker webhook receiver...")
print(f"Sending POST request to: {url}")
print(f"Payload: {json.dumps(test_payload, indent=2)}")

try:
    response = requests.post(url, json=test_payload, headers=headers, timeout=30)
    
    print(f"\n📊 Response Status: {response.status_code}")
    print(f"📊 Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        print("✅ SUCCESS: Webhook processed successfully!")
        try:
            response_json = response.json()
            print(f"📋 Response JSON: {json.dumps(response_json, indent=2)}")
        except:
            print(f"📋 Response Text: {response.text}")
    else:
        print(f"❌ ERROR: Status {response.status_code}")
        print(f"📋 Response Text: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ REQUEST ERROR: {e}")

print("\n🔍 Checking Docker logs for any errors...")