#!/usr/bin/env python3
"""
Test script for BigQuery GDELT integration with webhook pipeline
"""

import requests
import json
import sys

def test_bigquery_integration():
    """Test the BigQuery integration through the webhook"""
    
    # Test webhook URL (adjust as needed)
    webhook_url = "http://localhost:5005/webhook/letta"
    
    # Test queries that should trigger BigQuery
    test_queries = [
        {
            "name": "Global Events Query",
            "prompt": "What's happening in the world today? Any recent global events?",
            "should_trigger_bigquery": True
        },
        {
            "name": "USA Politics Query", 
            "prompt": "Tell me about recent political events involving the USA",
            "should_trigger_bigquery": True
        },
        {
            "name": "Weather Query",
            "prompt": "What's the weather like today?",
            "should_trigger_bigquery": False
        },
        {
            "name": "GDELT Direct Query",
            "prompt": "Show me recent GDELT data about international conflicts",
            "should_trigger_bigquery": True
        }
    ]
    
    print("Testing BigQuery Integration with Webhook Pipeline")
    print("=" * 60)
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print(f"Query: {test_case['prompt']}")
        print(f"Expected BigQuery Trigger: {test_case['should_trigger_bigquery']}")
        
        # Prepare webhook payload
        payload = {
            "prompt": test_case["prompt"],
            "max_nodes": 5,
            "max_facts": 10,
            "request": {
                "path": "/v1/agents/agent-test123/chat",
                "body": {
                    "messages": [
                        {
                            "role": "user",
                            "content": test_case["prompt"]
                        }
                    ]
                }
            }
        }
        
        try:
            print("Sending webhook request...")
            response = requests.post(
                webhook_url, 
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if BigQuery was triggered
                bigquery_result = result.get("bigquery")
                graphiti_result = result.get("graphiti")
                
                print(f"BigQuery Triggered: {bigquery_result is not None}")
                print(f"Graphiti Success: {graphiti_result.get('success', False) if graphiti_result else False}")
                
                if bigquery_result:
                    print(f"BigQuery Success: {bigquery_result.get('success', False)}")
                    print(f"BigQuery Block ID: {bigquery_result.get('block_id', 'N/A')}")
                    if not bigquery_result.get('success', False):
                        print(f"BigQuery Error: {bigquery_result.get('error', 'Unknown')}")
                
                # Verify expectation
                bigquery_triggered = bigquery_result is not None
                expectation_met = bigquery_triggered == test_case['should_trigger_bigquery']
                print(f"Expectation Met: {expectation_met}")
                
                if not expectation_met:
                    print(f"❌ FAIL: Expected BigQuery trigger = {test_case['should_trigger_bigquery']}, got {bigquery_triggered}")
                else:
                    print(f"✅ PASS: BigQuery trigger behavior as expected")
                    
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            
        print("-" * 40)

def test_bigquery_direct():
    """Test BigQuery functionality directly"""
    print("\nTesting BigQuery GDELT Integration Directly")
    print("=" * 50)
    
    try:
        from bigquery_gdelt_integration import (
            should_invoke_bigquery,
            generate_bigquery_context,
            execute_bigquery_search
        )
        
        # Test keyword detection
        test_messages = [
            "What's happening in the world today?",
            "Recent news about USA",
            "Tell me about global politics",
            "What's the weather like?",
            "Recent GDELT events"
        ]
        
        print("Testing keyword detection:")
        for msg in test_messages:
            should_trigger = should_invoke_bigquery(msg)
            print(f"  '{msg[:40]}...': {should_trigger}")
        
        # Test BigQuery execution
        print("\nTesting BigQuery execution:")
        result = execute_bigquery_search("example_3")
        print(f"Query success: {result['success']}")
        if result['success']:
            print(f"Number of results: {result['metadata'].get('num_results', 0)}")
        else:
            print(f"Error: {result['error']}")
            
        # Test context generation
        print("\nTesting context generation:")
        context = generate_bigquery_context("What are recent global events involving the USA?")
        if context:
            print(f"Context generated: {len(context)} characters")
            print(f"Preview: {context[:200]}...")
        else:
            print("No context generated")
            
    except ImportError as e:
        print(f"❌ Cannot import BigQuery integration: {e}")
    except Exception as e:
        print(f"❌ Error testing BigQuery directly: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "direct":
        test_bigquery_direct()
    else:
        print("Testing BigQuery Integration (use 'direct' argument for direct testing)")
        print("Make sure the webhook server is running on localhost:5005")
        print()
        
        # Test direct functionality first
        test_bigquery_direct()
        
        # Then test webhook integration
        try:
            test_bigquery_integration()
        except KeyboardInterrupt:
            print("\n\nTest interrupted by user")
        except Exception as e:
            print(f"\n\nTest failed with error: {e}")