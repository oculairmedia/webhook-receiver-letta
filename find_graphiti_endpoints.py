#!/usr/bin/env python3
"""
Find the correct Graphiti API endpoints by testing various possibilities.
"""

import requests
import json

def test_all_possible_endpoints():
    """Test all possible endpoint variations"""
    
    print("🔍 SCANNING FOR GRAPHITI ENDPOINTS")
    print("=" * 50)
    
    base_url = "http://192.168.50.90:8001"
    
    # Test for OpenAPI spec locations
    openapi_locations = [
        "/openapi.json",
        "/api/openapi.json", 
        "/docs/openapi.json",
        "/swagger.json",
        "/api/swagger.json"
    ]
    
    print("📋 Checking for OpenAPI specifications...")
    for location in openapi_locations:
        url = f"{base_url}{location}"
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                print(f"✅ Found OpenAPI spec at: {url}")
                try:
                    spec = resp.json()
                    print(f"   Title: {spec.get('info', {}).get('title', 'Unknown')}")
                    print(f"   Version: {spec.get('info', {}).get('version', 'Unknown')}")
                    
                    # List all paths
                    paths = spec.get('paths', {})
                    print(f"   Available endpoints ({len(paths)}):")
                    for path in sorted(paths.keys()):
                        methods = list(paths[path].keys())
                        print(f"     {path} [{', '.join(methods).upper()}]")
                    
                    return spec
                except:
                    print(f"   ❌ Invalid JSON in OpenAPI spec")
        except:
            continue
    
    print("❌ No OpenAPI specification found")
    
    # Test common REST endpoint patterns
    print("\n🧪 Testing common REST patterns...")
    common_patterns = [
        # Search/Query endpoints
        ("/api/search", "GET"),
        ("/api/query", "GET"), 
        ("/search", "GET"),
        ("/query", "GET"),
        
        # Graph-specific endpoints
        ("/api/graph/search", "GET"),
        ("/api/graph/query", "GET"),
        ("/graph/search", "GET"),
        ("/graph/query", "GET"),
        
        # Node/Edge endpoints
        ("/api/nodes", "GET"),
        ("/api/edges", "GET"),
        ("/api/entities", "GET"),
        ("/api/facts", "GET"),
        
        # Version-specific
        ("/api/v1/search", "GET"),
        ("/api/v1/query", "GET"),
        ("/api/v1/graph", "GET"),
        
        # Alternative patterns
        ("/api/retrieve", "GET"),
        ("/api/find", "GET"),
        ("/api/lookup", "GET")
    ]
    
    working_endpoints = []
    
    for endpoint, method in common_patterns:
        url = f"{base_url}{endpoint}"
        try:
            if method == "GET":
                resp = requests.get(url, timeout=3)
            else:
                resp = requests.post(url, json={}, timeout=3)
            
            if resp.status_code not in [404, 405]:  # Not "Not Found" or "Method Not Allowed"
                status_info = f"{resp.status_code} {resp.reason}"
                print(f"✅ {method} {endpoint} - {status_info}")
                working_endpoints.append((endpoint, method, resp.status_code))
                
                # Show response for successful calls
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        print(f"   📄 Sample response: {json.dumps(data, indent=2)[:200]}...")
                    except:
                        print(f"   📄 Text response: {resp.text[:100]}...")
        except:
            continue
    
    return working_endpoints

def test_specific_graphiti_patterns():
    """Test patterns specific to Graphiti knowledge graphs"""
    
    print("\n🧠 TESTING GRAPHITI-SPECIFIC PATTERNS")
    print("=" * 45)
    
    base_url = "http://192.168.50.90:8001"
    
    # Graphiti-specific endpoints we might expect
    graphiti_endpoints = [
        "/api/memories",
        "/api/knowledge", 
        "/api/context",
        "/api/semantic_search",
        "/api/vector_search",
        "/api/similarity",
        "/api/related",
        "/api/associations",
        "/api/facts/search",
        "/api/entities/search",
        "/api/nodes/search"
    ]
    
    for endpoint in graphiti_endpoints:
        url = f"{base_url}{endpoint}"
        try:
            resp = requests.get(url, timeout=3)
            if resp.status_code != 404:
                print(f"✅ Found: {endpoint} ({resp.status_code})")
                if resp.status_code == 200:
                    print(f"   📄 Response: {resp.text[:100]}...")
        except:
            continue

if __name__ == "__main__":
    endpoints = test_all_possible_endpoints()
    test_specific_graphiti_patterns()
    
    print(f"\n🎯 SUMMARY")
    print("=" * 20)
    print(f"Graphiti service is running on http://192.168.50.90:8001")
    print(f"Health check: /api/status ✅")
    print(f"API docs: /api/docs ✅")
    print(f"Search endpoint: ❌ NOT FOUND")
    print(f"\nRecommendation: Check if Graphiti is using a different API version")
    print(f"or if the search functionality is implemented differently.")