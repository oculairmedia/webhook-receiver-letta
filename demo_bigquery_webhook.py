#!/usr/bin/env python3
"""
Demo script showing BigQuery integration with the webhook pipeline
"""

import requests
import json
import time

def demo_bigquery_webhook():
    """Demonstrate BigQuery integration through webhook calls"""
    
    webhook_url = "http://localhost:5005/webhook/letta"
    
    # Demo queries that will trigger BigQuery
    demo_queries = [
        {
            "query": "What's happening globally today? Any major international events?",
            "description": "Global events query - should trigger BigQuery GDELT search"
        },
        {
            "query": "Tell me about recent political developments involving the USA",
            "description": "USA politics query - should invoke BigQuery for current events"
        },
        {
            "query": "What are recent GDELT events showing international cooperation?",
            "description": "Direct GDELT query - should definitely trigger BigQuery"
        }
    ]
    
    print("🚀 BigQuery GDELT Integration Demo")
    print("=" * 60)
    print("This demo shows how the Cerebras model can trigger BigQuery GDELT")
    print("searches when queries relate to global events, news, or geopolitics.")
    print()
    
    for i, demo in enumerate(demo_queries, 1):
        print(f"\n🔍 Demo {i}: {demo['description']}")
        print(f"Query: \"{demo['query']}\"")
        print("-" * 50)
        
        # Prepare webhook payload with agent context
        payload = {
            "prompt": demo["query"],
            "max_nodes": 5,
            "max_facts": 10,
            "request": {
                "path": "/v1/agents/agent-demo123/chat",
                "body": {
                    "messages": [
                        {
                            "role": "user", 
                            "content": demo["query"]
                        }
                    ]
                }
            }
        }
        
        try:
            print("📡 Sending to webhook pipeline...")
            start_time = time.time()
            
            response = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=45  # BigQuery can take a moment
            )
            
            elapsed = time.time() - start_time
            print(f"⏱️  Response time: {elapsed:.2f} seconds")
            print(f"📋 HTTP Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Check results
                graphiti_result = result.get("graphiti", {})
                bigquery_result = result.get("bigquery")
                
                print(f"✅ Overall Success: {result.get('success', False)}")
                print(f"🧠 Graphiti Block: {graphiti_result.get('success', False)} (ID: {graphiti_result.get('block_id', 'N/A')})")
                
                if bigquery_result:
                    print(f"📊 BigQuery Block: {bigquery_result.get('success', False)} (ID: {bigquery_result.get('block_id', 'N/A')})")
                    print(f"🎯 BigQuery Triggered: YES - Global events detected!")
                    
                    if not bigquery_result.get('success', False):
                        print(f"❌ BigQuery Error: {bigquery_result.get('error', 'Unknown')}")
                else:
                    print("🎯 BigQuery Triggered: NO - Query didn't match global event keywords")
                
                # Show agent info if available
                if result.get('agent_id'):
                    print(f"🤖 Agent: {result.get('agent_name', 'Unknown')} ({result.get('agent_id')})")
                
            else:
                print(f"❌ HTTP Error {response.status_code}")
                print(f"Response: {response.text[:300]}...")
                
        except requests.exceptions.Timeout:
            print("⏰ Request timed out - BigQuery might be taking longer than expected")
        except requests.exceptions.ConnectionError:
            print("🔌 Connection failed - make sure webhook server is running on localhost:5005")
        except Exception as e:
            print(f"💥 Unexpected error: {e}")
        
        if i < len(demo_queries):
            print("\n⏳ Waiting 2 seconds before next demo...")
            time.sleep(2)
    
    print("\n" + "=" * 60)
    print("🎉 Demo completed!")
    print("\n📝 Summary:")
    print("- Queries about global events, news, politics trigger BigQuery GDELT searches")
    print("- Both Graphiti (semantic memory) and BigQuery (structured data) blocks are created")
    print("- The Cerebras model gets access to both types of context for richer responses")
    print("- BigQuery blocks use label 'bigquery' while Graphiti uses 'graphiti_context'")
    print("\n🛠️  To customize:")
    print("- Edit keyword matching in bigquery_gdelt_integration.py")
    print("- Configure environment variables for BigQuery behavior")
    print("- Modify GDELT query types in the integration module")

if __name__ == "__main__":
    print("Starting BigQuery GDELT Integration Demo")
    print("Make sure the webhook server is running on localhost:5005")
    input("Press Enter to continue...")
    
    try:
        demo_bigquery_webhook()
    except KeyboardInterrupt:
        print("\n\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n\n💥 Demo failed: {e}")