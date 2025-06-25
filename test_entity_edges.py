#!/usr/bin/env python3

import requests
import json
import os

GRAPHITI_API_URL = os.environ.get("GRAPHITI_URL", "http://192.168.50.90:8001/api")

def find_emmanuel_entity():
    """Find Emmanuel entity in the knowledge graph"""
    print("=== Finding Emmanuel Entity ===")
    
    search_terms = ["Emmanuel", "emmanuel", "user", "Emmanuel user"]
    
    for term in search_terms:
        print(f"\n--- Searching for: '{term}' ---")
        
        search_url = f"{GRAPHITI_API_URL}/search/nodes"
        payload = {
            "query": term,
            "max_nodes": 20,
            "group_ids": []
        }
        
        try:
            response = requests.post(search_url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                nodes = result.get('nodes', [])
                print(f"Found {len(nodes)} nodes:")
                
                emmanuel_entities = []
                for node in nodes:
                    name = node.get('name', '').lower()
                    if 'emmanuel' in name:
                        emmanuel_entities.append(node)
                        print(f"  ✅ {node.get('name', 'N/A')} (UUID: {node.get('uuid', 'N/A')})")
                        print(f"     Summary: {node.get('summary', 'N/A')}")
                    else:
                        print(f"  • {node.get('name', 'N/A')} (UUID: {node.get('uuid', 'N/A')})")
                
                if emmanuel_entities:
                    return emmanuel_entities
                    
        except Exception as e:
            print(f"Error searching for {term}: {e}")
    
    return []

def get_entity_edges(entity_uuid):
    """Get all edges for a specific entity"""
    print(f"\n=== Getting Edges for Entity {entity_uuid} ===")
    
    # Try the entity-edge endpoint
    edge_url = f"{GRAPHITI_API_URL}/entity-edge/{entity_uuid}"
    
    try:
        response = requests.get(edge_url, timeout=30)
        print(f"Entity-edge GET status: {response.status_code}")
        
        if response.status_code == 200:
            edges_data = response.json()
            print(f"Response: {json.dumps(edges_data, indent=2)}")
            return edges_data
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error getting entity edges: {e}")
    
    return None

def search_facts_about_entity(entity_name):
    """Search for facts/relationships about the entity"""
    print(f"\n=== Searching Facts about {entity_name} ===")
    
    search_url = f"{GRAPHITI_API_URL}/search/facts"
    payload = {
        "query": entity_name,
        "max_facts": 50,
        "group_ids": []
    }
    
    try:
        response = requests.post(search_url, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            facts = result.get('facts', [])
            print(f"Found {len(facts)} facts:")
            
            relationships = []
            for fact in facts:
                summary = fact.get('summary', '')
                fact_uuid = fact.get('uuid', 'N/A')
                
                # Extract relationship information
                if any(rel_word in summary.lower() for rel_word in ['likes', 'loves', 'works', 'is', 'has', 'knows', 'uses', 'prefers']):
                    relationships.append({
                        'summary': summary,
                        'uuid': fact_uuid,
                        'fact': fact
                    })
                    print(f"  🔗 {summary}")
                else:
                    print(f"  • {summary}")
            
            return relationships
            
    except Exception as e:
        print(f"Error searching facts: {e}")
    
    return []

def analyze_relationship_patterns(facts):
    """Analyze the relationship patterns from facts"""
    print(f"\n=== Analyzing Relationship Patterns ===")
    
    relationship_types = {
        'likes': [],
        'loves': [],
        'works': [],
        'is': [],
        'has': [],
        'knows': [],
        'uses': [],
        'prefers': [],
        'other': []
    }
    
    for fact in facts:
        summary = fact['summary'].lower()
        categorized = False
        
        for rel_type in relationship_types.keys():
            if rel_type != 'other' and rel_type in summary:
                relationship_types[rel_type].append(fact['summary'])
                categorized = True
                break
        
        if not categorized:
            relationship_types['other'].append(fact['summary'])
    
    for rel_type, relationships in relationship_types.items():
        if relationships:
            print(f"\n{rel_type.upper()} relationships:")
            for rel in relationships:
                print(f"  • {rel}")

if __name__ == "__main__":
    # Step 1: Find Emmanuel entity
    emmanuel_entities = find_emmanuel_entity()
    
    if not emmanuel_entities:
        print("\n❌ Could not find Emmanuel entity in the knowledge graph")
        exit(1)
    
    # Step 2: Get edges for each Emmanuel entity found
    for entity in emmanuel_entities:
        entity_uuid = entity.get('uuid')
        entity_name = entity.get('name')
        
        if entity_uuid:
            edges_data = get_entity_edges(entity_uuid)
    
    # Step 3: Search for facts about Emmanuel
    facts = search_facts_about_entity("Emmanuel")
    
    # Step 4: Analyze relationship patterns
    if facts:
        analyze_relationship_patterns(facts)
    else:
        print("\n⚠️ No relationship facts found for Emmanuel")