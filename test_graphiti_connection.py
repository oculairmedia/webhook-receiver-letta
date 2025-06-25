#!/usr/bin/env python3

import requests
import json
import os

# Test Graphiti API connection and search functionality
GRAPHITI_API_URL = os.environ.get("GRAPHITI_URL", "http://192.168.50.90:8001/api")

def test_graphiti_connection():
    """Test basic connection to Graphiti API"""
    try:
        # Test basic health/info endpoint
        response = requests.get(f"{GRAPHITI_API_URL}/health", timeout=10)
        print(f"Graphiti health check status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.text}")
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Connection error: {e}")

def test_graphiti_search():
    """Test Graphiti search functionality"""
    try:
        # Test nodes search
        search_url_nodes = f"{GRAPHITI_API_URL}/search/nodes"
        nodes_payload = {
            "query": "test",
            "max_nodes": 5,
            "group_ids": []
        }
        
        print(f"Testing nodes search at: {search_url_nodes}")
        response = requests.post(search_url_nodes, json=nodes_payload, timeout=30)
        print(f"Nodes search status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Nodes found: {len(result.get('nodes', []))}")
            if result.get('nodes'):
                print(f"Sample node: {result['nodes'][0]}")
        else:
            print(f"Nodes search error: {response.text}")
            
        # Test facts search
        search_url_facts = f"{GRAPHITI_API_URL}/search/facts"
        facts_payload = {
            "query": "test",
            "max_facts": 5,
            "group_ids": []
        }
        
        print(f"Testing facts search at: {search_url_facts}")
        response = requests.post(search_url_facts, json=facts_payload, timeout=30)
        print(f"Facts search status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Facts found: {len(result.get('facts', []))}")
            if result.get('facts'):
                print(f"Sample fact: {result['facts'][0]}")
        else:
            print(f"Facts search error: {response.text}")
            
    except Exception as e:
        print(f"Search error: {e}")

def test_graphiti_data():
    """Test what data exists in Graphiti"""
    try:
        # Try to get some basic information about what's in the graph
        endpoints_to_try = [
            "/nodes",
            "/facts", 
            "/groups",
            "/episodes"
        ]
        
        for endpoint in endpoints_to_try:
            url = f"{GRAPHITI_API_URL}{endpoint}"
            print(f"Testing endpoint: {url}")
            try:
                response = requests.get(url, timeout=10)
                print(f"  Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"  Found {len(data)} items")
                    elif isinstance(data, dict):
                        print(f"  Response keys: {list(data.keys())}")
                        if 'nodes' in data:
                            print(f"  Nodes: {len(data.get('nodes', []))}")
                        if 'facts' in data:
                            print(f"  Facts: {len(data.get('facts', []))}")
                else:
                    print(f"  Error: {response.text}")
            except Exception as e:
                print(f"  Exception: {e}")
                
    except Exception as e:
        print(f"Data exploration error: {e}")

if __name__ == "__main__":
    print("=== Testing Graphiti Connection ===")
    test_graphiti_connection()
    
    print("\n=== Testing Graphiti Search ===")
    test_graphiti_search()
    
    print("\n=== Testing Graphiti Data ===")
    test_graphiti_data()