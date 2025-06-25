#!/usr/bin/env python3
"""
Test script to verify the deployed arXiv memory block separation fix
"""
import requests
import json

def test_deployed_arxiv_fix():
    """Test the deployed arXiv separation fix"""
    
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
    
    print("Testing deployed arXiv memory block separation fix...")
    print(f"Container URL: {webhook_url}")
    
    try:
        print("Sending webhook request...")
        response = requests.post(
            webhook_url,
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: Response received!")
            
            # Check arXiv result
            arxiv_result = result.get("arxiv")
            if arxiv_result and arxiv_result.get("success"):
                arxiv_block_id = arxiv_result.get("block_id")
                arxiv_block_name = arxiv_result.get("block_name")
                arxiv_message = arxiv_result.get("message", "")
                arxiv_updated = arxiv_result.get("updated", False)
                
                print(f"\nArXiv Integration:")
                print(f"  Status: SUCCESS")
                print(f"  Block ID: {arxiv_block_id}")
                print(f"  Block Name: {arxiv_block_name}")
                print(f"  Message: {arxiv_message}")
                print(f"  Updated existing: {arxiv_updated}")
                
                if "created successfully" in arxiv_message and not arxiv_updated:
                    print("  ✅ arXiv block was CREATED (not updated)")
                else:
                    print("  ❌ arXiv block was UPDATED (not created)")
            else:
                print(f"\nArXiv Integration: FAILED or not triggered")
                if arxiv_result:
                    print(f"  Reason: {arxiv_result.get('reason', 'unknown')}")
            
            # Check GDELT result  
            gdelt_result = result.get("gdelt")
            if gdelt_result and gdelt_result.get("success"):
                gdelt_block_id = gdelt_result.get("block_id")
                gdelt_block_name = gdelt_result.get("block_name")
                gdelt_message = gdelt_result.get("message", "")
                gdelt_updated = gdelt_result.get("updated", False)
                
                print(f"\nGDELT Integration:")
                print(f"  Status: SUCCESS")
                print(f"  Block ID: {gdelt_block_id}")
                print(f"  Block Name: {gdelt_block_name}")
                print(f"  Message: {gdelt_message}")
                print(f"  Updated existing: {gdelt_updated}")
                
                if "created successfully" in gdelt_message and not gdelt_updated:
                    print("  ✅ GDELT block was CREATED (not updated)")
                else:
                    print("  ❌ GDELT block was UPDATED (not created)")
            else:
                print(f"\nGDELT Integration: FAILED or not triggered")
            
            # Check Graphiti result
            graphiti_result = result.get("graphiti")
            if graphiti_result and graphiti_result.get("success"):
                graphiti_block_id = graphiti_result.get("block_id")
                graphiti_block_name = graphiti_result.get("block_name")
                
                print(f"\nGraphiti Integration:")
                print(f"  Status: SUCCESS")
                print(f"  Block ID: {graphiti_block_id}")
                print(f"  Block Name: {graphiti_block_name}")
            
            # Compare block IDs
            all_block_ids = []
            if arxiv_result and arxiv_result.get("success"):
                all_block_ids.append(("arXiv", arxiv_result.get("block_id")))
            if gdelt_result and gdelt_result.get("success"):
                all_block_ids.append(("GDELT", gdelt_result.get("block_id")))
            if graphiti_result and graphiti_result.get("success"):
                all_block_ids.append(("Graphiti", graphiti_result.get("block_id")))
            
            print(f"\nBlock ID Comparison:")
            for service, block_id in all_block_ids:
                print(f"  {service}: {block_id}")
            
            # Check for uniqueness
            block_ids_only = [bid for _, bid in all_block_ids]
            unique_block_ids = set(block_ids_only)
            
            if len(unique_block_ids) == len(block_ids_only):
                print(f"\n✅ SUCCESS: All {len(block_ids_only)} services are using DIFFERENT block IDs!")
                print("   The memory block separation fix is working correctly!")
            else:
                print(f"\n❌ ISSUE: {len(block_ids_only)} services but only {len(unique_block_ids)} unique block IDs")
                print("   Some services are still sharing blocks")
            
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_deployed_arxiv_fix()