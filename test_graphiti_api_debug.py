#!/usr/bin/env python3
"""
Debug script to test Graphiti API connectivity and endpoints.
"""

import requests
import json

def test_graphiti_connectivity():
    """Test various Graphiti API endpoints to diagnose the 404 issue"""
    
    print("🔍 GRAPHITI API CONNECTIVITY TEST")
    print("=" * 60)
    
    base_url = "http://192.168.50.90:8001"
    endpoints_to_test = [
        "/",
        "/api",
        "/api/health",
        "/api/search",
        "/health",
        "/docs",
        "/api/docs"
    ]
    
    print(f"🎯 Testing base URL: {base_url}")
    print()
    
    for endpoint in endpoints_to_test:
        url = f"{base_url}{endpoint}"
        print(f"📍 Testing: {url}")
        
        try:
            # Test GET request first
            response = requests.get(url, timeout=5)
            print(f"   ✅ GET {response.status_code} - {response.reason}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   📄 JSON Response: {json.dumps(data, indent=2)[:200]}...")
                except:
                    print(f"   📄 Text Response: {response.text[:200]}...")
            
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection Error - Service not reachable")
        except requests.exceptions.Timeout:
            print(f"   ⏱️ Timeout - Service not responding")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    # Test the specific search endpoint that's failing
    print("🔎 TESTING SPECIFIC SEARCH ENDPOINT")
    print("-" * 40)
    
    search_url = f"{base_url}/api/search"
    test_params = {
        "query": "test query",
        "max_nodes": 8,
        "max_facts": 20
    }
    
    print(f"📍 Testing: {search_url}")
    print(f"📦 Params: {test_params}")
    
    try:
        response = requests.get(search_url, params=test_params, timeout=10)
        print(f"   📊 Status: {response.status_code}")
        print(f"   📄 Response: {response.text[:500]}...")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_alternative_ports():
    """Test common alternative ports for Graphiti"""
    
    print("\n🔄 TESTING ALTERNATIVE PORTS")
    print("=" * 40)
    
    host = "192.168.50.90"
    ports_to_test = [8000, 8001, 8002, 8080, 8081, 3000, 5000]
    
    for port in ports_to_test:
        url = f"http://{host}:{port}/api/search"
        print(f"📍 Testing port {port}: {url}")
        
        try:
            response = requests.get(url, timeout=3)
            print(f"   ✅ {response.status_code} - Service found!")
            if response.status_code != 404:
                print(f"   📄 Response: {response.text[:100]}...")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ No service on port {port}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_graphiti_connectivity()
    test_alternative_ports()