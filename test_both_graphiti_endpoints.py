#!/usr/bin/env python3

import requests
import json
import os
from datetime import datetime

GRAPHITI_API_URL = os.environ.get("GRAPHITI_URL", "http://192.168.50.90:8001/api")

def test_existing_endpoints():
    """Test the existing endpoints we've been using"""
    print("=== Testing Existing Endpoints ===")
    
    try:
        # Test existing search/nodes endpoint
        search_url_nodes = f"{GRAPHITI_API_URL}/search/nodes"
        nodes_payload = {
            "query": "meridian agent",
            "max_nodes": 5,
            "group_ids": []
        }
        
        print(f"Testing: {search_url_nodes}")
        response = requests.post(search_url_nodes, json=nodes_payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Nodes found: {len(result.get('nodes', []))}")
            if result.get('nodes'):
                for node in result['nodes'][:3]:
                    print(f"  - {node.get('name', 'N/A')}: {node.get('summary', 'N/A')}")
        else:
            print(f"Error: {response.text}")
            
        # Test existing search/facts endpoint
        search_url_facts = f"{GRAPHITI_API_URL}/search/facts"
        facts_payload = {
            "query": "meridian agent",
            "max_facts": 5,
            "group_ids": []
        }
        
        print(f"Testing: {search_url_facts}")
        response = requests.post(search_url_facts, json=facts_payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Facts found: {len(result.get('facts', []))}")
            if result.get('facts'):
                for fact in result['facts'][:3]:
                    print(f"  - {fact.get('summary', 'N/A')}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error testing existing endpoints: {e}")

def test_new_endpoints():
    """Test the new endpoints from the OpenAPI schema"""
    print("\n=== Testing New OpenAPI Endpoints ===")
    
    try:
        # Test /search endpoint
        search_url = f"{GRAPHITI_API_URL}/search"
        search_payload = {
            "query": "meridian agent",
            "max_facts": 10,
            "group_ids": None  # Search all groups
        }
        
        print(f"Testing: {search_url}")
        response = requests.post(search_url, json=search_payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Search result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            print(f"Result: {json.dumps(result, indent=2)[:500]}...")
        else:
            print(f"Error: {response.text}")
            
        # Test /get-memory endpoint
        get_memory_url = f"{GRAPHITI_API_URL}/get-memory"
        
        # We need to provide a message to build the retrieval query
        memory_payload = {
            "group_id": "default",  # Try with a default group
            "max_facts": 10,
            "center_node_uuid": None,
            "messages": [
                {
                    "content": "Tell me about the meridian agent",
                    "role_type": "user",
                    "role": "user",
                    "timestamp": datetime.now().isoformat()
                }
            ]
        }
        
        print(f"Testing: {get_memory_url}")
        response = requests.post(get_memory_url, json=memory_payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Memory result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            print(f"Result: {json.dumps(result, indent=2)[:500]}...")
        else:
            print(f"Error: {response.text}")
            
        # Test healthcheck
        health_url = f"{GRAPHITI_API_URL}/healthcheck"
        print(f"Testing: {health_url}")
        response = requests.get(health_url, timeout=10)
        print(f"Health status: {response.status_code}")
        if response.status_code == 200:
            print(f"Health response: {response.json()}")
            
    except Exception as e:
        print(f"Error testing new endpoints: {e}")

def test_episodes_with_group():
    """Test episodes endpoint with different group IDs"""
    print("\n=== Testing Episodes with Groups ===")
    
    try:
        # Try different group IDs
        group_ids_to_try = ["default", "main", "user", "agent", ""]
        
        for group_id in group_ids_to_try:
            episodes_url = f"{GRAPHITI_API_URL}/episodes/{group_id}"
            params = {"last_n": 10}
            
            print(f"Testing episodes for group '{group_id}': {episodes_url}")
            response = requests.get(episodes_url, params=params, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                episodes = result.get('episodes', []) if isinstance(result, dict) else result
                print(f"  Found {len(episodes)} episodes")
                if episodes:
                    for i, episode in enumerate(episodes[:3]):
                        print(f"    Episode {i+1}: {episode.get('name', 'N/A')}")
                    break  # Found episodes, stop trying other groups
            elif response.status_code == 404:
                print(f"  Group '{group_id}' not found")
            else:
                print(f"  Error: {response.text}")
                
    except Exception as e:
        print(f"Error testing episodes: {e}")

if __name__ == "__main__":
    test_existing_endpoints()
    test_new_endpoints()
    test_episodes_with_group()