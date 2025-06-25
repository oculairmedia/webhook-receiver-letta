import requests
import json
import time

def test_simple_webhook():
    print("TESTING SIMPLE WEBHOOK RECEIVER")
    print("=" * 50)
    
    # Test payload focusing on the Graphiti search functionality
    test_payload = {
        "type": "stream_started",
        "timestamp": "2025-06-14T06:50:00.000Z",
        "prompt": [
            {
                "type": "text",
                "text": "Tell me about emmanuel umukoro"
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
                                "text": "Tell me about emmanuel umukoro"
                            }
                        ]
                    }
                ]
            }
        },
        "response": {
            "type": "stream_started",
            "id": "test_msg_456",
            "stream_id": "test_stream_456"
        }
    }
    
    # Send the webhook
    webhook_url = "http://localhost:5005/webhook/letta"
    headers = {'Content-Type': 'application/json'}
    
    print(f"Sending webhook to: {webhook_url}")
    print(f"Payload: {json.dumps(test_payload, indent=2)}")
    print()
    
    try:
        response = requests.post(webhook_url, json=test_payload, headers=headers, timeout=30)
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("\n✓ SUCCESS: Webhook processed successfully!")
            print("Check the terminal running flask_webhook_receiver.py for detailed logs")
        else:
            print(f"\n✗ FAILED: Webhook returned {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n✗ ERROR: Failed to send webhook: {e}")

if __name__ == "__main__":
    test_simple_webhook()