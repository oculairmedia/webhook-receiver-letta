#!/usr/bin/env python3

import requests
import json
import os

GRAPHITI_API_URL = os.environ.get("GRAPHITI_URL", "http://192.168.50.90:8001/api")

def test_various_search_terms():
    """Test with various search terms that might be in the graph"""
    print("=== Testing Various Search Terms ===")
    
    search_terms = [
        "meridian",
        "agent", 
        "graphiti",
        "context",
        "user",
        "assistant",
        "working",
        "improving",
        "hey",
        "good",
        "pretty",
        "test",
        "",  # Empty search
        "*",  # Wildcard
        "the",  # Common word
        "a",   # Very common word
    ]
    
    for term in search_terms:
        print(f"\n--- Searching for: '{term}' ---")
        
        # Test nodes
        search_url_nodes = f"{GRAPHITI_API_URL}/search/nodes"
        nodes_payload = {
            "query": term,
            "max_nodes": 10,
            "group_ids": []
        }
        
        try:
            response = requests.post(search_url_nodes, json=nodes_payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                nodes = result.get('nodes', [])
                print(f"  Nodes: {len(nodes)} found")
                if nodes:
                    for node in nodes[:3]:
                        print(f"    - {node.get('name', 'N/A')}: {node.get('summary', 'N/A')[:100]}...")
                    return  # Found something, stop here
            else:
                print(f"  Nodes error: {response.status_code}")
        except Exception as e:
            print(f"  Nodes exception: {e}")
            
        # Test facts
        search_url_facts = f"{GRAPHITI_API_URL}/search/facts"
        facts_payload = {
            "query": term,
            "max_facts": 10,
            "group_ids": []
        }
        
        try:
            response = requests.post(search_url_facts, json=facts_payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                facts = result.get('facts', [])
                print(f"  Facts: {len(facts)} found")
                if facts:
                    for fact in facts[:3]:
                        print(f"    - {fact.get('summary', 'N/A')[:100]}...")
                    return  # Found something, stop here
            else:
                print(f"  Facts error: {response.status_code}")
        except Exception as e:
            print(f"  Facts exception: {e}")

def test_different_parameters():
    """Test with different search parameters"""
    print("\n=== Testing Different Parameters ===")
    
    base_query = "meridian"
    
    parameter_sets = [
        {"max_nodes": 100, "group_ids": []},
        {"max_nodes": 1, "group_ids": []},
        {"max_nodes": 10, "group_ids": None},
        {"max_nodes": 10},  # No group_ids
        {"max_nodes": 10, "group_ids": ["default"]},
        {"max_nodes": 10, "group_ids": ["main"]},
        {"max_nodes": 10, "group_ids": ["user"]},
        {"max_nodes": 10, "group_ids": [""]},
    ]
    
    for i, params in enumerate(parameter_sets):
        print(f"\n--- Parameter Set {i+1}: {params} ---")
        
        search_url = f"{GRAPHITI_API_URL}/search/nodes"
        payload = {"query": base_query, **params}
        
        try:
            response = requests.post(search_url, json=payload, timeout=30)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                nodes = result.get('nodes', [])
                print(f"  Nodes found: {len(nodes)}")
                if nodes:
                    for node in nodes[:2]:
                        print(f"    - {node.get('name', 'N/A')}")
                    return  # Found something, stop here
            else:
                print(f"  Error: {response.text}")
        except Exception as e:
            print(f"  Exception: {e}")

def test_raw_endpoints():
    """Test raw endpoints to see if data exists at all"""
    print("\n=== Testing Raw Data Endpoints ===")
    
    endpoints = [
        "/search/nodes",
        "/search/facts", 
        "/episodes/",
        "/episodes",
    ]
    
    for endpoint in endpoints:
        url = f"{GRAPHITI_API_URL}{endpoint}"
        print(f"\n--- Testing {endpoint} ---")
        
        # Try GET request first
        try:
            response = requests.get(url, timeout=10)
            print(f"  GET Status: {response.status_code}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        print(f"  Response keys: {list(data.keys())}")
                        for key, value in data.items():
                            if isinstance(value, list):
                                print(f"    {key}: {len(value)} items")
                            else:
                                print(f"    {key}: {type(value)}")
                    elif isinstance(data, list):
                        print(f"  List with {len(data)} items")
                        if data:
                            print(f"    Sample item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not a dict'}")
                except:
                    print(f"  Response text (first 200 chars): {response.text[:200]}")
        except Exception as e:
            print(f"  GET Exception: {e}")
            
        # Try POST with minimal payload
        if "search" in endpoint:
            try:
                minimal_payload = {"query": ""}
                response = requests.post(url, json=minimal_payload, timeout=10)
                print(f"  POST (empty query) Status: {response.status_code}")
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, dict):
                            for key, value in data.items():
                                if isinstance(value, list):
                                    print(f"    {key}: {len(value)} items")
                                    if value:
                                        return  # Found data!
                    except:
                        pass
            except Exception as e:
                print(f"  POST Exception: {e}")

if __name__ == "__main__":
    test_various_search_terms()
    test_different_parameters()
    test_raw_endpoints()