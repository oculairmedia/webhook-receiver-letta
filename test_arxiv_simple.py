#!/usr/bin/env python3
"""
Simple test script to verify arXiv memory block separation fix
"""
import requests
import json

def test_arxiv_separation():
    """Test that arXiv papers create separate memory blocks"""
    
    # Test webhook payload that should trigger arXiv search
    test_payload = {
        "request": {
            "path": "/v1/agents/agent-1eacfc07-d8b6-4f25-a6ee-aab71934e07a/messages",
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
    
    try:
        print("Sending webhook request...")
        response = requests.post(
            webhook_url,
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Response received successfully!")
            print(f"Full response: {json.dumps(result, indent=2)}")
            
            # Check if arXiv was triggered and created separate block
            arxiv_result = result.get("arxiv")
            if arxiv_result:
                if arxiv_result.get("success"):
                    print("\nSUCCESS: arXiv search was triggered and succeeded")
                    print(f"arXiv Block ID: {arxiv_result.get('block_id')}")
                    print(f"arXiv Block type: {arxiv_result.get('block_type')}")
                    print(f"arXiv Block name: {arxiv_result.get('block_name')}")
                else:
                    print(f"\narXiv search was triggered but failed: {arxiv_result.get('reason', 'unknown')}")
            else:
                print("\narXiv search was not triggered")
            
            # Check Graphiti result
            graphiti_result = result.get("graphiti")
            if graphiti_result and graphiti_result.get("success"):
                print("\nGraphiti context created successfully")
                print(f"Graphiti Block ID: {graphiti_result.get('block_id')}")
                print(f"Graphiti Block name: {graphiti_result.get('block_name')}")
            
            # Compare block IDs
            arxiv_block_id = arxiv_result.get('block_id') if arxiv_result else None
            graphiti_block_id = graphiti_result.get('block_id') if graphiti_result else None
            
            if arxiv_block_id and graphiti_block_id:
                if arxiv_block_id == graphiti_block_id:
                    print(f"\nWARNING: arXiv and Graphiti are using the SAME block ID: {arxiv_block_id}")
                    print("This indicates the separation fix is NOT working correctly!")
                else:
                    print(f"\nSUCCESS: arXiv and Graphiti are using DIFFERENT block IDs:")
                    print(f"  arXiv Block ID: {arxiv_block_id}")
                    print(f"  Graphiti Block ID: {graphiti_block_id}")
                    print("The separation fix is working correctly!")
            
        else:
            print(f"Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_arxiv_separation()