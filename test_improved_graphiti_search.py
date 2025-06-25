#!/usr/bin/env python3
"""
Test the improved Graphiti search implementation matching the reference tool.
"""

import requests
import json

def test_improved_graphiti_search():
    """Test Graphiti search using the improved parameters"""
    
    print("🔍 TESTING IMPROVED GRAPHITI SEARCH")
    print("=" * 50)
    
    base_url = "http://192.168.50.90:8001/api"
    
    test_queries = [
        "gdelt",
        "test", 
        "resume",
        "project",
        "*",  # Wildcard search
        ""    # Empty search
    ]
    
    for query in test_queries:
        print(f"\n📝 Testing query: '{query}'")
        print("-" * 30)
        
        # Test nodes with improved parameters
        nodes_payload = {
            "query": query,
            "max_nodes": 10,
            "group_ids": []  # Empty list means search all groups
        }
        
        try:
            nodes_response = requests.post(
                f"{base_url}/search/nodes", 
                json=nodes_payload, 
                timeout=15
            )
            print(f"Nodes - Status: {nodes_response.status_code}")
            
            if nodes_response.status_code == 200:
                nodes_data = nodes_response.json()
                print(f"Nodes - Response type: {type(nodes_data)}")
                print(f"Nodes - Keys: {list(nodes_data.keys()) if isinstance(nodes_data, dict) else 'list'}")
                
                # Handle different response formats
                if isinstance(nodes_data, list):
                    node_count = len(nodes_data)
                    nodes_list = nodes_data
                else:
                    node_count = len(nodes_data.get("results", []))
                    nodes_list = nodes_data.get("results", [])
                
                print(f"Nodes - Count: {node_count}")
                
                if nodes_list:
                    sample = nodes_list[0]
                    print(f"Nodes - Sample keys: {list(sample.keys())}")
                    print(f"Nodes - Sample: {json.dumps(sample, indent=2)[:300]}...")
            else:
                print(f"Nodes - Error: {nodes_response.text[:200]}")
                
        except Exception as e:
            print(f"Nodes - Exception: {e}")
        
        # Test facts with improved parameters  
        facts_payload = {
            "query": query,
            "max_facts": 10,  # Use max_facts instead of limit
            "group_ids": []   # Empty list means search all groups
        }
        
        try:
            facts_response = requests.post(
                f"{base_url}/search/facts", 
                json=facts_payload, 
                timeout=15
            )
            print(f"Facts - Status: {facts_response.status_code}")
            
            if facts_response.status_code == 200:
                facts_data = facts_response.json()
                
                # Handle different response formats
                if isinstance(facts_data, list):
                    fact_count = len(facts_data)
                    facts_list = facts_data
                else:
                    fact_count = len(facts_data.get("results", []))
                    facts_list = facts_data.get("results", [])
                    
                print(f"Facts - Count: {fact_count}")
                
                if facts_list:
                    sample = facts_list[0]
                    print(f"Facts - Sample: {json.dumps(sample, indent=2)[:200]}...")
            else:
                print(f"Facts - Error: {facts_response.text[:200]}")
                
        except Exception as e:
            print(f"Facts - Exception: {e}")

def test_episodes_detailed():
    """Test episodes endpoint in detail to understand data structure"""
    
    print(f"\n📚 TESTING EPISODES DETAILED")
    print("=" * 35)
    
    base_url = "http://192.168.50.90:8001/api"
    
    try:
        response = requests.get(f"{base_url}/episodes", timeout=10)
        print(f"Episodes status: {response.status_code}")
        
        if response.status_code == 200:
            episodes = response.json()
            print(f"Episodes type: {type(episodes)}")
            print(f"Episodes count: {len(episodes)}")
            
            if episodes:
                print("\nFirst episode structure:")
                first_episode = episodes[0]
                print(f"Keys: {list(first_episode.keys())}")
                
                for key, value in first_episode.items():
                    value_str = str(value)
                    if len(value_str) > 100:
                        value_str = value_str[:100] + "..."
                    print(f"  {key}: {value_str}")
        else:
            print(f"Episodes error: {response.text}")
            
    except Exception as e:
        print(f"Episodes exception: {e}")

def test_different_search_strategies():
    """Try different search strategies to find any data"""
    
    print(f"\n🧪 TESTING ALTERNATIVE SEARCH STRATEGIES")
    print("=" * 45)
    
    base_url = "http://192.168.50.90:8001/api"
    
    # Try different parameter combinations
    strategies = [
        {"query": "test", "max_nodes": 50},
        {"query": "test", "max_nodes": 100},
        {"query": "", "max_nodes": 20},
        {"query": "*", "max_nodes": 20},
        {"query": "a", "max_nodes": 20},
        {"query": "Test", "max_nodes": 20},  # Capital T
        {"query": "data", "max_nodes": 20}
    ]
    
    for strategy in strategies:
        print(f"\nStrategy: {strategy}")
        
        try:
            response = requests.post(
                f"{base_url}/search/nodes",
                json=strategy,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else len(data.get("results", []))
                print(f"  Result: {count} nodes found")
                
                if count > 0:
                    print("  SUCCESS! Found some nodes")
                    results = data if isinstance(data, list) else data.get("results", [])
                    for i, result in enumerate(results[:3]):
                        name = result.get('name', 'N/A')
                        summary = result.get('summary', 'N/A')[:50]
                        print(f"    {i+1}. {name}: {summary}...")
                    break
            else:
                print(f"  Error: {response.status_code}")
                
        except Exception as e:
            print(f"  Exception: {e}")

if __name__ == "__main__":
    test_improved_graphiti_search()
    test_episodes_detailed()
    test_different_search_strategies()