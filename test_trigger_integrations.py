#!/usr/bin/env python3
"""
Test script to specifically trigger GDELT and arXiv integrations
"""

import requests
import json
import sys
import time

def test_specific_triggers(webhook_url="http://localhost:5000"):
    """Test specific queries that should trigger GDELT and arXiv"""
    
    print(f"🎯 TESTING SPECIFIC INTEGRATION TRIGGERS")
    print(f"Webhook URL: {webhook_url}")
    print("=" * 60)
    
    # Test cases designed to trigger specific integrations
    test_cases = [
        {
            "name": "GDELT News Trigger Test",
            "description": "Should trigger GDELT news search",
            "payload": {
                "request": {
                    "body": {
                        "messages": [
                            {"role": "user", "content": "What's happening in the news today? Any breaking news or current events?"}
                        ]
                    },
                    "path": "/v1/agents/agent-9c48bb82-46e3-4be6-80eb-8ca43e3a68b6/messages"
                }
            },
            "expected_triggers": ["gdelt", "bigquery"]
        },
        {
            "name": "arXiv Academic Trigger Test", 
            "description": "Should trigger arXiv paper search",
            "payload": {
                "request": {
                    "body": {
                        "messages": [
                            {"role": "user", "content": "Find recent research papers on transformer architectures and attention mechanisms"}
                        ]
                    },
                    "path": "/v1/agents/agent-9c48bb82-46e3-4be6-80eb-8ca43e3a68b6/messages"
                }
            },
            "expected_triggers": ["arxiv"]
        },
        {
            "name": "Strong News Keywords Test",
            "description": "Strong news-related keywords", 
            "payload": {
                "request": {
                    "body": {
                        "messages": [
                            {"role": "user", "content": "Tell me about recent political developments and international conflicts in the news"}
                        ]
                    },
                    "path": "/v1/agents/agent-9c48bb82-46e3-4be6-80eb-8ca43e3a68b6/messages"
                }
            },
            "expected_triggers": ["gdelt", "bigquery"]
        },
        {
            "name": "Strong Academic Keywords Test",
            "description": "Strong academic research keywords",
            "payload": {
                "request": {
                    "body": {
                        "messages": [
                            {"role": "user", "content": "Show me recent academic papers about deep learning optimization and neural network architectures"}
                        ]
                    },
                    "path": "/v1/agents/agent-9c48bb82-46e3-4be6-80eb-8ca43e3a68b6/messages"
                }
            },
            "expected_triggers": ["arxiv"]
        },
        {
            "name": "Multiple Triggers Test",
            "description": "Should trigger both GDELT and arXiv",
            "payload": {
                "request": {
                    "body": {
                        "messages": [
                            {"role": "user", "content": "What are the latest news about AI research and recent academic papers on machine learning?"}
                        ]
                    },
                    "path": "/v1/agents/agent-9c48bb82-46e3-4be6-80eb-8ca43e3a68b6/messages"
                }
            },
            "expected_triggers": ["gdelt", "bigquery", "arxiv"]
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Description: {test_case['description']}")
        print(f"   Expected triggers: {', '.join(test_case['expected_triggers'])}")
        print(f"   Query: {test_case['payload']['request']['body']['messages'][0]['content']}")
        
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
                result = response.json()
                print(f"   ✅ Webhook successful")
                
                # Analyze what was actually triggered
                triggered = []
                
                if result.get('gdelt', {}).get('triggered') or 'gdelt' in str(result).lower():
                    triggered.append('gdelt')
                if result.get('bigquery', {}).get('triggered') or 'bigquery' in str(result).lower():
                    triggered.append('bigquery')
                if result.get('arxiv', {}).get('triggered') or 'arxiv' in str(result).lower():
                    triggered.append('arxiv')
                
                # Check response keys for clues
                response_keys = list(result.keys())
                print(f"   📋 Response keys: {response_keys}")
                
                if 'block_id' in result:
                    print(f"   🗃️  Block created/updated: {result['block_id']}")
                if 'message' in result:
                    print(f"   💬 Message: {result['message'][:100]}...")
                
                # Check for trigger indicators
                if triggered:
                    print(f"   🎯 Triggered: {', '.join(triggered)}")
                else:
                    print(f"   ⚠️  No clear trigger indicators found")
                
                # Compare expected vs actual
                missing_triggers = set(test_case['expected_triggers']) - set(triggered)
                if missing_triggers:
                    print(f"   ❌ Missing expected triggers: {', '.join(missing_triggers)}")
                else:
                    print(f"   ✅ All expected triggers activated!")
                
                results.append({
                    "test": test_case['name'],
                    "expected": test_case['expected_triggers'],
                    "triggered": triggered,
                    "response_time": end_time - start_time,
                    "success": len(missing_triggers) == 0
                })
                
            else:
                print(f"   ❌ Webhook failed")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('error', 'Unknown')}")
                except:
                    print(f"   Raw response: {response.text[:200]}...")
                    
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Wait between tests to avoid overwhelming the server
        if i < len(test_cases):
            print("   Waiting 3 seconds before next test...")
            time.sleep(3)
    
    # Summary
    print(f"\n" + "="*60)
    print(f"📊 TEST SUMMARY")
    print(f"="*60)
    
    successful_tests = sum(1 for r in results if r['success'])
    total_tests = len(results)
    
    print(f"Total tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['test']}: Expected {result['expected']} → Got {result['triggered']}")
    
    if successful_tests == total_tests:
        print("\n🎉 All integration triggers working correctly!")
    else:
        print(f"\n⚠️  Some integration triggers may need adjustment")
        print("💡 Check the webhook server logs for detailed trigger analysis")

def analyze_trigger_conditions():
    """Analyze what conditions should trigger each integration"""
    print("\n" + "="*60)
    print("🔍 TRIGGER CONDITION ANALYSIS")
    print("="*60)
    
    print("\n📰 GDELT/BigQuery Triggers:")
    print("   Should trigger on: news, current events, breaking, politics, conflicts")
    print("   Keywords: news, today, happening, current, breaking, political, conflict")
    
    print("\n📚 arXiv Triggers:")
    print("   Should trigger on: research, papers, academic, scientific terms")
    print("   Keywords: papers, research, academic, study, algorithm, neural, transformer")
    
    print("\n💡 If triggers aren't working:")
    print("   1. Check the trigger threshold settings in the webhook code")
    print("   2. Verify the keyword matching logic")
    print("   3. Check if external APIs (GDELT, arXiv) are accessible")
    print("   4. Review the server logs for trigger evaluation details")

if __name__ == "__main__":
    webhook_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    print("🧪 INTEGRATION TRIGGER TESTING")
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
    
    # Run trigger tests
    test_specific_triggers(webhook_url)
    
    # Show analysis
    analyze_trigger_conditions()
    
    print("\n🔍 Next steps:")
    print("1. Check the webhook server terminal for detailed trigger evaluation logs")
    print("2. If triggers aren't working, check the trigger threshold settings")
    print("3. Verify external API accessibility (GDELT, arXiv)")