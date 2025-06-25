#!/usr/bin/env python3
"""
Test script for GDELT integration with the webhook system
"""

import requests
import json
import sys
from datetime import datetime


def test_gdelt_webhook_integration(webhook_url: str = "http://localhost:5005/webhook/letta"):
    """Test the GDELT integration through the webhook"""
    
    print("Testing GDELT Integration with Webhook System")
    print("=" * 60)
    
    # Test cases designed to trigger different GDELT categories
    test_cases = [
        {
            "name": "Global Events Query",
            "prompt": "What's happening in the world today? Any recent global events?",
            "expected_gdelt_trigger": True,
            "expected_category": "global_events"
        },
        {
            "name": "Ukraine Conflict Query",
            "prompt": "Tell me about recent developments in the Ukraine conflict",
            "expected_gdelt_trigger": True,
            "expected_category": "conflicts"
        },
        {
            "name": "Global Markets Query",
            "prompt": "How are global financial markets performing this week?",
            "expected_gdelt_trigger": True,
            "expected_category": "economics"
        },
        {
            "name": "AI Technology Query",
            "prompt": "What are the latest AI breakthroughs in the news?",
            "expected_gdelt_trigger": True,
            "expected_category": "technology"
        },
        {
            "name": "Natural Disaster Query",
            "prompt": "Any recent earthquakes or natural disasters globally?",
            "expected_gdelt_trigger": True,
            "expected_category": "disasters"
        },
        {
            "name": "Weather Query (No Trigger)",
            "prompt": "What's the weather like today in New York?",
            "expected_gdelt_trigger": False,
            "expected_category": None
        },
        {
            "name": "Math Query (No Trigger)",
            "prompt": "What's 2 + 2?",
            "expected_gdelt_trigger": False,
            "expected_category": None
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print("-" * 50)
        print(f"Query: {test_case['prompt']}")
        print(f"Expected GDELT Trigger: {test_case['expected_gdelt_trigger']}")
        if test_case['expected_category']:
            print(f"Expected Category: {test_case['expected_category']}")
        
        # Prepare webhook payload
        payload = {
            "prompt": test_case["prompt"],
            "max_nodes": 5,
            "max_facts": 10,
            "request": {
                "path": "/v1/agents/agent-gdelt-test/chat",
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
                
                # Check GDELT results
                gdelt_result = result.get("gdelt")
                graphiti_result = result.get("graphiti")
                bigquery_result = result.get("bigquery")
                
                # Analyze GDELT trigger behavior
                gdelt_triggered = gdelt_result is not None
                gdelt_success = gdelt_result.get("success", False) if gdelt_result else False
                
                print(f"GDELT Triggered: {gdelt_triggered}")
                if gdelt_triggered:
                    print(f"GDELT Success: {gdelt_success}")
                    if gdelt_success:
                        print(f"GDELT Block ID: {gdelt_result.get('block_id', 'N/A')}")
                        gdelt_category = gdelt_result.get('metadata', {}).get('category', 'Unknown')
                        print(f"GDELT Category: {gdelt_category}")
                        gdelt_query = gdelt_result.get('metadata', {}).get('query', 'Unknown')
                        print(f"GDELT Query Used: {gdelt_query}")
                    else:
                        print(f"GDELT Error: {gdelt_result.get('error', 'Unknown error')}")
                
                print(f"Graphiti Success: {graphiti_result.get('success', False) if graphiti_result else False}")
                print(f"BigQuery Triggered: {bigquery_result is not None}")
                if bigquery_result:
                    print(f"BigQuery Success: {bigquery_result.get('success', False)}")
                
                # Verify expectations
                expectation_met = gdelt_triggered == test_case['expected_gdelt_trigger']
                
                if expectation_met:
                    print(f"✅ PASS: GDELT trigger behavior as expected")
                    
                    # If GDELT was triggered and successful, check category
                    if gdelt_triggered and gdelt_success and test_case['expected_category']:
                        actual_category = gdelt_result.get('metadata', {}).get('category', '')
                        if actual_category == test_case['expected_category']:
                            print(f"✅ PASS: Category match ({actual_category})")
                        else:
                            print(f"⚠️  PARTIAL: Category mismatch. Expected: {test_case['expected_category']}, Got: {actual_category}")
                else:
                    print(f"❌ FAIL: Expected GDELT trigger = {test_case['expected_gdelt_trigger']}, got {gdelt_triggered}")
                
                # Store results for summary
                test_result = {
                    "test_name": test_case['name'],
                    "prompt": test_case['prompt'],
                    "expected_trigger": test_case['expected_gdelt_trigger'],
                    "actual_trigger": gdelt_triggered,
                    "gdelt_success": gdelt_success if gdelt_triggered else None,
                    "expectation_met": expectation_met,
                    "category": gdelt_result.get('metadata', {}).get('category') if gdelt_triggered and gdelt_success else None
                }
                results.append(test_result)
                
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                results.append({
                    "test_name": test_case['name'],
                    "error": f"HTTP {response.status_code}",
                    "expectation_met": False
                })
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            results.append({
                "test_name": test_case['name'],
                "error": str(e),
                "expectation_met": False
            })
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            results.append({
                "test_name": test_case['name'],
                "error": str(e),
                "expectation_met": False
            })
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r.get('expectation_met', False))
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    print("\nDetailed Results:")
    for result in results:
        status = "✅ PASS" if result.get('expectation_met', False) else "❌ FAIL"
        test_name = result['test_name']
        print(f"  {status} - {test_name}")
        
        if 'error' in result:
            print(f"    Error: {result['error']}")
        elif result.get('actual_trigger'):
            category = result.get('category', 'Unknown')
            success = result.get('gdelt_success', False)
            print(f"    GDELT: Triggered, Success: {success}, Category: {category}")
        else:
            print(f"    GDELT: Not triggered (as expected)" if result.get('expectation_met') else "    GDELT: Not triggered (unexpected)")
    
    # Test integration health
    print(f"\n{'='*60}")
    print("INTEGRATION HEALTH CHECK")
    print("="*60)
    
    gdelt_tests = [r for r in results if r.get('expected_trigger', False)]
    if gdelt_tests:
        gdelt_working = sum(1 for r in gdelt_tests if r.get('actual_trigger', False) and r.get('gdelt_success', False))
        print(f"GDELT API Integration: {gdelt_working}/{len(gdelt_tests)} working")
        
        if gdelt_working > 0:
            print("✅ GDELT API integration is functional")
        else:
            print("❌ GDELT API integration may have issues")
    
    return results


def test_webhook_server_health(webhook_url: str = "http://localhost:5005"):
    """Test if the webhook server is running"""
    try:
        health_url = f"{webhook_url}/health"
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            print(f"✅ Webhook server is healthy at {webhook_url}")
            return True
        else:
            print(f"⚠️  Webhook server responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print(f"❌ Cannot connect to webhook server at {webhook_url}")
        return False


if __name__ == "__main__":
    webhook_base_url = "http://localhost:5005"
    webhook_endpoint = f"{webhook_base_url}/webhook/letta"
    
    if len(sys.argv) > 1:
        webhook_base_url = sys.argv[1].rstrip('/')
        webhook_endpoint = f"{webhook_base_url}/webhook/letta"
    
    print("GDELT Webhook Integration Test")
    print("=" * 40)
    print(f"Webhook URL: {webhook_endpoint}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check server health first
    if not test_webhook_server_health(webhook_base_url):
        print("\n⚠️  Warning: Webhook server may not be running.")
        print("   Start the server with: python flask_webhook_receiver.py")
        print("   Then rerun this test.")
        sys.exit(1)
    
    # Run the integration tests
    try:
        results = test_gdelt_webhook_integration(webhook_endpoint)
        
        # Exit with appropriate code
        passed = sum(1 for r in results if r.get('expectation_met', False))
        if passed == len(results):
            print(f"\n🎉 All tests passed! GDELT integration is working correctly.")
            sys.exit(0)
        else:
            print(f"\n⚠️  Some tests failed. Check the webhook server logs for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        sys.exit(1)