#!/usr/bin/env python3
"""
Test script to verify arXiv memory block separation fix
"""
import requests
import json
import time

def test_arxiv_separation():
    """Test that arXiv papers create separate memory blocks"""
    
    # Test webhook payload that should trigger arXiv search
    test_payload = {
        "request": {
            "path": "/v1/agents/agent-test-arxiv-separation/messages",
            "body": {
                "messages": [
                    {
                        "role": "user",
                        "content": "Tell me about recent advances in machine learning optimization techniques"
                    }
                ]
            }
        },
        "max_nodes": 8,
        "max_facts": 20
    }
    
    webhook_url = "http://localhost:5005/webhook/letta"
    
    print("Testing arXiv memory block separation fix...")
    print(f"Webhook URL: {webhook_url}")
    print(f"Test payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        print("\nSending webhook request...")
        response = requests.post(
            webhook_url,
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Check if arXiv was triggered and created separate block
            arxiv_result = result.get("arxiv")
            if arxiv_result:
                if arxiv_result.get("success"):
                    print("\n✅ SUCCESS: arXiv search was triggered and succeeded")
                    print(f"   Block ID: {arxiv_result.get('block_id')}")
                    print(f"   Block type: {arxiv_result.get('block_type')}")
                    print(f"   Papers found: {arxiv_result.get('papers_found', 'unknown')}")
                else:
                    print(f"\n❌ arXiv search was triggered but failed: {arxiv_result.get('reason', 'unknown')}")
            else:
                print("\n❌ arXiv search was not triggered")
            
            # Check Graphiti result
            graphiti_result = result.get("graphiti")
            if graphiti_result and graphiti_result.get("success"):
                print(f"\n✅ Graphiti context created successfully")
                print(f"   Block ID: {graphiti_result.get('block_id')}")
            
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_arxiv_separation()