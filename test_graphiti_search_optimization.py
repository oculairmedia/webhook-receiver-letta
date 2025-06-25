#!/usr/bin/env python3
"""
Test and optimize Graphiti search parameters to improve retrieval quality.
"""

import requests
import json

def test_graphiti_search_optimization():
    """Test different search strategies to improve Graphiti retrieval"""
    
    print("🔍 TESTING GRAPHITI SEARCH OPTIMIZATION")
    print("=" * 60)
    
    base_url = "http://192.168.50.90:8001/api"
    
    # Test queries of varying complexity
    test_queries = [
        "gdelt",
        "news",
        "global events", 
        "technology",
        "test",
        "resume",
        "project",
        "data",
        "simple query"
    ]
    
    # Test different search parameters
    search_params = [
        {"limit": 5},
        {"limit": 10},
        {"limit": 20},
        {"limit": 5, "threshold": 0.1},
        {"limit": 10, "threshold": 0.05}
    ]
    
    print("🧪 Testing node search with different parameters...")
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        print("-" * 30)
        
        for params in search_params:
            try:
                search_payload = {
                    "query": query,
                    **params
                }
                
                # Test nodes endpoint
                nodes_response = requests.post(
                    f"{base_url}/search/nodes", 
                    json=search_payload, 
                    timeout=10
                )
                
                if nodes_response.status_code == 200:
                    nodes_data = nodes_response.json()
                    node_count = len(nodes_data) if isinstance(nodes_data, list) else len(nodes_data.get("results", []))
                    
                    # Test facts endpoint
                    facts_response = requests.post(
                        f"{base_url}/search/facts", 
                        json=search_payload, 
                        timeout=10
                    )
                    
                    facts_count = 0
                    if facts_response.status_code == 200:
                        facts_data = facts_response.json()
                        facts_count = len(facts_data) if isinstance(facts_data, list) else len(facts_data.get("results", []))
                    
                    print(f"   {params}: nodes={node_count}, facts={facts_count}")
                    
                    # Show sample results if any found
                    if node_count > 0:
                        sample_nodes = nodes_data if isinstance(nodes_data, list) else nodes_data.get("results", [])
                        if sample_nodes:
                            sample = sample_nodes[0]
                            name = sample.get('name', 'N/A')
                            summary = sample.get('summary', 'N/A')[:100]
                            print(f"      Sample: {name} - {summary}...")
                
                else:
                    print(f"   {params}: ERROR {nodes_response.status_code}")
                    
            except Exception as e:
                print(f"   {params}: EXCEPTION {str(e)}")
    
    # Test if we can get a list of all entities
    print(f"\n🗂️ CHECKING AVAILABLE DATA")
    print("=" * 40)
    
    try:
        # Try broad searches to see what's available
        broad_searches = ["", " ", "*", "a", "the"]
        
        for broad_query in broad_searches:
            try:
                payload = {"query": broad_query, "limit": 20}
                response = requests.post(f"{base_url}/search/nodes", json=payload, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data if isinstance(data, list) else data.get("results", [])
                    print(f"Broad query '{broad_query}': {len(results)} nodes found")
                    
                    if results:
                        print("Sample entities:")
                        for i, item in enumerate(results[:3]):
                            name = item.get('name', 'N/A')
                            entity_type = item.get('type', 'N/A')
                            print(f"  {i+1}. {name} (type: {entity_type})")
                        break
                        
            except Exception as e:
                continue
    
    except Exception as e:
        print(f"Error checking available data: {e}")

def test_episodes_endpoint():
    """Test the episodes endpoint to see what data is available"""
    
    print(f"\n📚 TESTING EPISODES ENDPOINT")
    print("=" * 35)
    
    base_url = "http://192.168.50.90:8001/api"
    
    try:
        response = requests.get(f"{base_url}/episodes", timeout=10)
        print(f"Episodes endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            episodes = response.json()
            print(f"Found {len(episodes)} episodes")
            
            if episodes:
                print("Sample episodes:")
                for i, episode in enumerate(episodes[:3]):
                    episode_id = episode.get('uuid', 'N/A')
                    content = str(episode.get('content', ''))[:100]
                    print(f"  {i+1}. {episode_id}: {content}...")
        else:
            print(f"Episodes response: {response.text[:200]}")
            
    except Exception as e:
        print(f"Error testing episodes: {e}")

if __name__ == "__main__":
    test_graphiti_search_optimization()
    test_episodes_endpoint()