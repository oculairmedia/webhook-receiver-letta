#!/usr/bin/env python3
"""
Test memory block operations specifically to debug the full webhook flow
"""

import requests
import json
import sys
import time

def test_letta_connection(letta_base_url="https://letta2.oculair.ca", password="lettaSecurePass123"):
    """Test direct connection to Letta API"""
    print(f"🔗 TESTING LETTA API CONNECTION")
    print(f"Base URL: {letta_base_url}")
    print("=" * 60)
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-BARE-PASSWORD": f"password {password}",
        "Authorization": f"Bearer {password}"
    }
    
    # Test basic connectivity
    print("\n1. Testing basic connectivity...")
    try:
        response = requests.get(f"{letta_base_url}/v1/health", headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Response: {response.text}")
        else:
            print("   ✅ Letta API is accessible")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False
    
    # Test agents endpoint
    print("\n2. Testing agents endpoint...")
    try:
        response = requests.get(f"{letta_base_url}/v1/agents", headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            agents = response.json()
            print(f"   ✅ Found {len(agents)} agents")
            if agents:
                print(f"   First agent ID: {agents[0].get('id', 'N/A')}")
                return agents[0].get('id')  # Return first agent ID for testing
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Agents endpoint failed: {e}")
    
    # Test blocks endpoint
    print("\n3. Testing blocks endpoint...")
    try:
        response = requests.get(f"{letta_base_url}/v1/blocks", headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            blocks = response.json()
            print(f"   ✅ Found {len(blocks)} blocks")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Blocks endpoint failed: {e}")
    
    return None

def test_full_webhook_with_memory_operations(webhook_url="http://localhost:5000", agent_id=None):
    """Test the full webhook receiver (not debug version) with memory operations"""
    print(f"\n🧠 TESTING FULL WEBHOOK WITH MEMORY OPERATIONS")
    print(f"Webhook URL: {webhook_url}")
    print("=" * 60)
    
    if not agent_id:
        agent_id = "test-agent-12345"  # Use a test agent ID
        print(f"⚠️  Using test agent ID: {agent_id}")
    else:
        print(f"✅ Using real agent ID: {agent_id}")
    
    test_cases = [
        {
            "name": "Basic context generation with agent ID",
            "payload": {
                "request": {
                    "body": {
                        "messages": [
                            {"role": "user", "content": "Tell me about machine learning"}
                        ]
                    },
                    "path": f"/v1/agents/{agent_id}/messages"
                }
            },
            "expected_operations": ["context_generation", "memory_block_update"]
        },
        {
            "name": "arXiv trigger test",
            "payload": {
                "request": {
                    "body": {
                        "messages": [
                            {"role": "user", "content": "Find recent papers about transformers on arXiv"}
                        ]
                    },
                    "path": f"/v1/agents/{agent_id}/messages"
                }
            },
            "expected_operations": ["context_generation", "arxiv_search", "memory_block_update"]
        },
        {
            "name": "GDELT/BigQuery trigger test",
            "payload": {
                "request": {
                    "body": {
                        "messages": [
                            {"role": "user", "content": "What's happening in the news about artificial intelligence?"}
                        ]
                    },
                    "path": f"/v1/agents/{agent_id}/messages"
                }
            },
            "expected_operations": ["context_generation", "gdelt_search", "memory_block_update"]
        }
    ]
    
    for test_case in test_cases:
        print(f"\n   Testing: {test_case['name']}")
        print(f"   Expected operations: {', '.join(test_case['expected_operations'])}")
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{webhook_url}/webhook/letta",
                json=test_case['payload'],
                headers={"Content-Type": "application/json"},
                timeout=60  # Longer timeout for memory operations
            )
            end_time = time.time()
            
            print(f"   Status: {response.status_code}")
            print(f"   Response time: {end_time - start_time:.2f}s")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Webhook successful")
                
                # Analyze response
                operations_performed = []
                
                if 'context_length' in result:
                    operations_performed.append("context_generation")
                    print(f"   📊 Context length: {result['context_length']}")
                
                if result.get('arxiv_triggered'):
                    operations_performed.append("arxiv_search")
                    print(f"   📚 arXiv triggered: {result['arxiv_triggered']}")
                
                if result.get('gdelt_triggered') or result.get('bigquery_triggered'):
                    operations_performed.append("gdelt_search")
                    print(f"   📰 GDELT/BigQuery triggered")
                
                if result.get('memory_updated') or result.get('block_created') or result.get('block_updated'):
                    operations_performed.append("memory_block_update")
                    print(f"   🧠 Memory operations performed")
                
                if result.get('errors'):
                    print(f"   ⚠️  Errors encountered: {result['errors']}")
                
                # Check if expected operations were performed
                missing_operations = set(test_case['expected_operations']) - set(operations_performed)
                if missing_operations:
                    print(f"   ⚠️  Missing expected operations: {', '.join(missing_operations)}")
                else:
                    print(f"   ✅ All expected operations performed")
                
            else:
                print(f"   ❌ Webhook failed")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('error', 'Unknown')}")
                    if 'traceback' in error_data:
                        print(f"   Traceback preview: {error_data['traceback'][:200]}...")
                except:
                    print(f"   Raw response: {response.text[:200]}...")
                    
        except Exception as e:
            print(f"   ❌ Exception: {e}")

def start_full_webhook_server():
    """Helper to start the full webhook server (not debug version)"""
    print("\n🚀 STARTING FULL WEBHOOK SERVER")
    print("=" * 50)
    print("Note: You should run this in a separate terminal:")
    print("python flask_webhook_receiver.py --host 0.0.0.0 --port 5000")
    print("\nWaiting 5 seconds for you to start the server...")
    time.sleep(5)

def test_webhook_server_selection():
    """Test both debug and full webhook servers to compare behavior"""
    print("\n🔄 COMPARING DEBUG vs FULL WEBHOOK SERVERS")
    print("=" * 60)
    
    test_payload = {
        "request": {
            "body": {
                "messages": [
                    {"role": "user", "content": "Test message for comparison"}
                ]
            },
            "path": "/v1/agents/comparison-test/messages"
        }
    }
    
    servers = [
        {"name": "Debug Server", "url": "http://localhost:5005", "description": "Debug version with simplified logic"},
        {"name": "Full Server", "url": "http://localhost:5000", "description": "Full version with memory operations"}
    ]
    
    for server in servers:
        print(f"\n   Testing {server['name']} ({server['description']})")
        print(f"   URL: {server['url']}")
        
        try:
            # Test health first
            health_response = requests.get(f"{server['url']}/health", timeout=5)
            if health_response.status_code != 200:
                print(f"   ❌ Server not healthy")
                continue
            
            # Test webhook
            response = requests.post(
                f"{server['url']}/webhook/letta",
                json=test_payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Success")
                print(f"   Response keys: {list(result.keys())}")
                if 'context_length' in result:
                    print(f"   Context length: {result['context_length']}")
            else:
                print(f"   ❌ Failed: {response.text[:100]}...")
                
        except requests.exceptions.ConnectionError:
            print(f"   ⚠️  Server not running")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 MEMORY BLOCK OPERATIONS TEST SUITE")
    print("=" * 70)
    
    # Test 1: Letta API connection
    agent_id = test_letta_connection()
    
    # Test 2: Compare debug vs full webhook servers
    test_webhook_server_selection()
    
    # Test 3: Full webhook testing (if server is available)
    print("\n" + "="*70)
    print("💡 INSTRUCTIONS FOR FULL TESTING:")
    print("1. Stop the debug server (Ctrl+C in the terminal)")
    print("2. Start the full server: python flask_webhook_receiver.py --host 0.0.0.0 --port 5000")
    print("3. Run this test again to see memory block operations in action")
    print("4. Or manually test with: python test_complete_webhook_flow.py http://localhost:5000")
    
    # Check if full server is running
    try:
        response = requests.get("http://localhost:5000/health", timeout=2)
        if response.status_code == 200:
            print("\n✅ Full server detected! Running memory operations tests...")
            test_full_webhook_with_memory_operations("http://localhost:5000", agent_id)
        else:
            print("\n⚠️  Full server not responding properly")
    except:
        print("\n⚠️  Full server not running")
    
    print("\n🎉 Memory block operations test completed!")