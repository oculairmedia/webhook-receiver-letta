#!/usr/bin/env python3
"""
Check Graphiti API documentation to find correct endpoints.
"""

import requests
import json

def check_api_docs():
    """Check the API documentation for available endpoints"""
    
    print("📚 CHECKING GRAPHITI API DOCUMENTATION")
    print("=" * 50)
    
    docs_url = "http://192.168.50.90:8001/api/docs"
    
    try:
        response = requests.get(docs_url, timeout=10)
        if response.status_code == 200:
            print("✅ Successfully retrieved API docs")
            
            # Try to find OpenAPI spec
            openapi_url = "http://192.168.50.90:8001/openapi.json"
            try:
                spec_response = requests.get(openapi_url, timeout=5)
                if spec_response.status_code == 200:
                    spec = spec_response.json()
                    print("\n🔍 AVAILABLE ENDPOINTS:")
                    print("-" * 30)
                    
                    paths = spec.get('paths', {})
                    for path, methods in paths.items():
                        print(f"📍 {path}")
                        for method, details in methods.items():
                            summary = details.get('summary', 'No description')
                            print(f"   {method.upper()}: {summary}")
                        print()
                    
                    return spec
                else:
                    print(f"❌ OpenAPI spec not available: {spec_response.status_code}")
            except Exception as e:
                print(f"❌ Error fetching OpenAPI spec: {e}")
            
        else:
            print(f"❌ Cannot access API docs: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return None

def test_common_endpoints():
    """Test common API endpoint patterns"""
    
    print("\n🧪 TESTING COMMON ENDPOINT PATTERNS")
    print("=" * 40)
    
    base_url = "http://192.168.50.90:8001"
    
    # Common endpoint patterns
    endpoints_to_test = [
        "/search",
        "/query", 
        "/api/v1/search",
        "/api/v1/query",
        "/graphiti/search",
        "/graphiti/query",
        "/graph/search",
        "/graph/query"
    ]
    
    for endpoint in endpoints_to_test:
        url = f"{base_url}{endpoint}"
        print(f"📍 Testing: {url}")
        
        try:
            # Test both GET and POST
            for method in ['GET', 'POST']:
                try:
                    if method == 'GET':
                        resp = requests.get(url, timeout=3)
                    else:
                        resp = requests.post(url, 
                                           json={"query": "test"}, 
                                           timeout=3)
                    
                    if resp.status_code != 404:
                        print(f"   ✅ {method} {resp.status_code} - Found!")
                        if resp.status_code == 200:
                            print(f"   📄 Response: {resp.text[:100]}...")
                        break
                except:
                    continue
            else:
                print(f"   ❌ Not found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def check_root_endpoints():
    """Check what's available at the root level"""
    
    print("\n🏠 CHECKING ROOT LEVEL ENDPOINTS")
    print("=" * 35)
    
    base_url = "http://192.168.50.90:8001"
    
    try:
        # Check if there's a different docs endpoint
        for path in ["/docs", "/swagger", "/redoc", "/api-docs"]:
            url = f"{base_url}{path}"
            try:
                resp = requests.get(url, timeout=3)
                if resp.status_code == 200:
                    print(f"✅ Found docs at: {url}")
            except:
                continue
        
        # Check for health/status endpoints
        for path in ["/health", "/status", "/ping", "/api/health", "/api/status"]:
            url = f"{base_url}{path}"
            try:
                resp = requests.get(url, timeout=3)
                if resp.status_code == 200:
                    print(f"✅ Found health endpoint: {url}")
                    print(f"   Response: {resp.text[:100]}")
            except:
                continue
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    spec = check_api_docs()
    test_common_endpoints()
    check_root_endpoints()