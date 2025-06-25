#!/usr/bin/env python3
"""
Test script for the new webhook structure provided by the user.
This script sends a test webhook payload matching the sample format to the receiver.
"""

import requests
import json

def test_new_webhook_structure():
    """Test the new webhook structure against the current receiver."""
    
    # Your sample webhook payload
    sample_payload = {
        "type": "message_sent",
        "timestamp": "2023-10-27T10:00:00Z",
        "prompt": "Hello, this is a test message.",
        "request": {
            "path": "/v1/agents/some-agent-id/messages",
            "method": "POST",
            "body": {
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello, this is a test message."
                    }
                ]
            }
        },
        "response": {
            "id": "msg_01H5ZEM5NJC6ZJ6B6ZJ6B6ZJ6B",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "This is a sample response from the assistant."
                }
            ],
            "model": "claude-2",
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 20,
                "output_tokens": 15
            }
        }
    }
    
    # Test against current receiver
    webhook_url = "http://127.0.0.1:5005/webhook/letta"
    
    print("Testing new webhook structure...")
    print(f"Webhook URL: {webhook_url}")
    print(f"Payload: {json.dumps(sample_payload, indent=2)}")
    print("-" * 50)
    
    try:
        response = requests.post(
            webhook_url,
            json=sample_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("SUCCESS: Webhook processed successfully!")
            print(f"Response: {json.dumps(response_data, indent=2)}")
        else:
            print(f"ERROR: Unexpected status code")
            print(f"Response text: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to webhook receiver. Is it running on port 5005?")
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out")
    except Exception as e:
        print(f"ERROR: {str(e)}")

def test_enhanced_webhook_structure():
    """Test an enhanced version with more fields from your sample."""
    
    enhanced_payload = {
        "type": "message_sent",
        "timestamp": "2025-06-08T04:43:00Z",
        "prompt": "Tell me about artificial intelligence and machine learning.",
        "request": {
            "path": "/v1/agents/agent-9c48bb82-46e3-4be6-80eb-8ca43e3a68b6/messages",
            "method": "POST",
            "body": {
                "messages": [
                    {
                        "role": "user",
                        "content": "Tell me about artificial intelligence and machine learning."
                    }
                ]
            }
        },
        "response": {
            "id": "msg_01H5ZEM5NJC6ZJ6B6ZJ6B6ZJ6B",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "Artificial Intelligence (AI) and Machine Learning (ML) are transformative technologies..."
                }
            ],
            "model": "claude-2",
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 45,
                "output_tokens": 150
            }
        },
        "max_nodes": 10,
        "max_facts": 25
    }
    
    webhook_url = "http://127.0.0.1:5005/webhook/letta"
    
    print("\n" + "="*60)
    print("Testing enhanced webhook structure...")
    print(f"Webhook URL: {webhook_url}")
    print(f"Enhanced payload with max_nodes/max_facts")
    print("-" * 50)
    
    try:
        response = requests.post(
            webhook_url,
            json=enhanced_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("SUCCESS: Enhanced webhook processed successfully!")
            
            # Extract key information
            if 'graphiti' in response_data:
                graphiti_result = response_data['graphiti']
                print(f"Graphiti Success: {graphiti_result.get('success', False)}")
                print(f"Block ID: {graphiti_result.get('block_id', 'N/A')}")
                print(f"Block Name: {graphiti_result.get('block_name', 'N/A')}")
                
            if 'arxiv' in response_data and response_data['arxiv']:
                arxiv_result = response_data['arxiv']
                print(f"arXiv Success: {arxiv_result.get('success', False)}")
                
            if 'agent_id' in response_data:
                print(f"Agent ID: {response_data['agent_id']}")
                
        else:
            print(f"ERROR: Status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    print("Testing New Webhook Structure")
    print("=" * 60)
    
    # Test basic structure
    test_new_webhook_structure()
    
    # Test enhanced structure
    test_enhanced_webhook_structure()
    
    print("\n" + "="*60)
    print("Testing completed!")