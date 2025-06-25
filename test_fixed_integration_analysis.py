#!/usr/bin/env python3
"""
Fixed test to properly analyze integration triggers
"""

import requests
import json
import sys
import time

def test_specific_triggers(webhook_url="http://localhost:5000"):
    """Test specific queries and properly analyze responses"""
    
    print(f"🎯 INTEGRATION TRIGGER ANALYSIS")
    print(f"Webhook URL: {webhook_url}")
    print("=" * 60)
    
    # Test cases designed to trigger specific integrations
    test_cases = [
        {
            "name": "Pure Academic Query (should trigger arXiv)",
            "description": "Should trigger arXiv without news keywords",
            "payload": {
                "request": {
                    "body": {
                        "messages": [
                            {"role": "user", "content": "Find research papers on transformer architectures and attention mechanisms"}
                        ]
                    },
                    "path": "/v1/agents/agent-9c48bb82-46e3-4be6-80eb-8ca43e3a68b6/messages"
                }
            },
            "expected_triggers": ["arxiv"]
        },
        {
            "name": "Pure News Query (should trigger GDELT)",
            "description": "Should trigger GDELT news search",
            "payload": {
                "request": {
                    "body": {
                        "messages": [
                            {"role": "user", "content": "What breaking events are happening globally today?"}
                        ]
                    },
                    "path": "/v1/agents/agent-9c48bb82-46e3-4be6-80eb-8ca43e3a68b6/messages"
                }
            },
            "expected_triggers": ["gdelt"]
        },
        {
            "name": "Academic Papers Query",
            "description": "Academic focus without news keywords",
            "payload": {
                "request": {
                    "body": {
                        "messages": [
                            {"role": "user", "content": "Show me recent academic papers about neural networks and deep learning"}
                        ]
                    },
                    "path": "/v1/agents/agent-9c48bb82-46e3-4be6-80eb-8ca43e3a68b6/messages"
                }
            },
            "expected_triggers": ["arxiv"]
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Query: {test_case['payload']['request']['body']['messages'][0]['content']}")
        print(f"   Expected: {', '.join(test_case['expected_triggers'])}")
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{webhook_url}/webhook/letta",
                json=test_case['payload'],
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            end_time = time.time()
            
            print(f"   Status: {response.status_code}")
            print(f"   Response time: {end_time - start_time:.2f}s")
            
            if response.status_code == 200:
                # Get the response data
                try:
                    result = response.json()
                    print(f"   ✅ Webhook successful")
                    
                    # Check response structure
                    if result is None:
                        print(f"   ⚠️  Response is None")
                        continue
                        
                    # Look for success indicators
                    success = result.get('success', False)
                    block_id = result.get('block_id', 'N/A')
                    message = result.get('message', 'No message')
                    
                    print(f"   📋 Success: {success}")
                    print(f"   🗃️  Block ID: {block_id}")
                    print(f"   💬 Message: {message[:100]}...")
                    
                    # Analyze what was actually triggered based on response structure
                    triggered = []
                    
                    # Look for integration-specific indicators in the response
                    response_str = json.dumps(result).lower()
                    
                    if 'gdelt' in response_str or 'news' in response_str:
                        triggered.append('gdelt')
                    if 'arxiv' in response_str or 'papers' in response_str:
                        triggered.append('arxiv')
                    if 'bigquery' in response_str:
                        triggered.append('bigquery')
                    
                    if triggered:
                        print(f"   🎯 Detected triggers: {', '.join(triggered)}")
                    else:
                        print(f"   ❓ No clear trigger indicators in response")
                    
                    # Compare expected vs actual
                    missing_triggers = set(test_case['expected_triggers']) - set(triggered)
                    if missing_triggers:
                        print(f"   ❌ Missing expected triggers: {', '.join(missing_triggers)}")
                        success = False
                    else:
                        print(f"   ✅ Expected triggers detected!")
                        success = True
                    
                    results.append({
                        "test": test_case['name'],
                        "expected": test_case['expected_triggers'],
                        "detected": triggered,
                        "response_time": end_time - start_time,
                        "success": success
                    })
                    
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON decode error: {e}")
                    print(f"   Raw response: {response.text[:200]}...")
                    
            else:
                print(f"   ❌ Webhook failed with status {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('error', 'Unknown')}")
                except:
                    print(f"   Raw response: {response.text[:200]}...")
                    
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Wait between tests
        if i < len(test_cases):
            print("   Waiting 3 seconds...")
            time.sleep(3)
    
    # Summary
    print(f"\n" + "="*60)
    print(f"📊 INTEGRATION TRIGGER ANALYSIS SUMMARY")
    print(f"="*60)
    
    successful_tests = sum(1 for r in results if r['success'])
    total_tests = len(results)
    
    print(f"Total tests: {total_tests}")
    print(f"Working correctly: {successful_tests}")
    print(f"Need fixes: {total_tests - successful_tests}")
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['test']}")
        print(f"    Expected: {result['expected']} → Detected: {result['detected']}")
    
    return results

def analyze_logs_findings():
    """Analyze what we learned from the server logs"""
    print("\n" + "="*60)
    print("🔍 ANALYSIS FROM SERVER LOGS")
    print("="*60)
    
    print("\n✅ GDELT Integration:")
    print("   • IS working - triggers successfully")
    print("   • Creates/updates gdelt_news memory blocks")
    print("   • Query: '(breaking news OR major event OR international) tone<-2'")
    print("   • Triggered by global events category")
    
    print("\n❌ arXiv Integration:")
    print("   • NOT working - being blocked by exclusion logic")
    print("   • Log shows: 'Not triggered: excluded: contains 'news''")
    print("   • Problem: queries with 'news' keyword exclude arXiv")
    print("   • Need to test with pure academic queries")
    
    print("\n⚠️  BigQuery Integration:")
    print("   • Log shows: 'BigQuery invocation not needed for this query'")
    print("   • May need different trigger conditions")
    
    print("\n🔧 RECOMMENDED FIXES:")
    print("   1. Adjust arXiv trigger logic to not exclude when 'papers'/'research' are present")
    print("   2. Test arXiv with pure academic queries (no 'news' keyword)")
    print("   3. Verify BigQuery trigger conditions")
    print("   4. Check if external APIs (arXiv, GDELT) are accessible")

if __name__ == "__main__":
    webhook_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    print("🧪 INTEGRATION TRIGGER ANALYSIS")
    print("=" * 70)
    
    # Check server health first
    try:
        response = requests.get(f"{webhook_url}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Webhook server not healthy: {response.status_code}")
            sys.exit(1)
        print("✅ Webhook server is healthy")
    except Exception as e:
        print(f"❌ Cannot connect to webhook server: {e}")
        sys.exit(1)
    
    # Analyze findings from logs first
    analyze_logs_findings()
    
    # Run targeted tests
    results = test_specific_triggers(webhook_url)
    
    print("\n🎯 NEXT STEPS:")
    print("1. Monitor the webhook server terminal for trigger evaluation logs")
    print("2. Check if arXiv triggers with pure academic queries (no 'news' keyword)")
    print("3. Verify if the exclusion logic needs adjustment")