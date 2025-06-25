#!/usr/bin/env python3

import requests
import json
import os
import re

GRAPHITI_API_URL = os.environ.get("GRAPHITI_URL", "http://192.168.50.90:8001/api")

def extract_relationships_from_summaries():
    """Extract relationship information from Emmanuel entity summaries"""
    print("=== Extracting Emmanuel Relationships from Summaries ===")
    
    # Search for Emmanuel entities
    search_url = f"{GRAPHITI_API_URL}/search/nodes"
    payload = {
        "query": "Emmanuel",
        "max_nodes": 20,
        "group_ids": []
    }
    
    try:
        response = requests.post(search_url, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            nodes = result.get('nodes', [])
            
            # Filter for Emmanuel entities
            emmanuel_entities = [node for node in nodes if 'emmanuel' in node.get('name', '').lower()]
            
            print(f"Found {len(emmanuel_entities)} Emmanuel entities")
            
            # Extract relationships from all summaries
            all_relationships = {}
            
            for entity in emmanuel_entities:
                summary = entity.get('summary', '')
                relationships = extract_relationships_from_text(summary)
                
                for rel_type, relations in relationships.items():
                    if rel_type not in all_relationships:
                        all_relationships[rel_type] = set()
                    all_relationships[rel_type].update(relations)
            
            # Display organized relationships
            display_relationships(all_relationships)
            
            return all_relationships
            
    except Exception as e:
        print(f"Error: {e}")
    
    return {}

def extract_relationships_from_text(text):
    """Extract relationship patterns from text"""
    relationships = {
        'personal': set(),
        'professional': set(), 
        'skills': set(),
        'projects': set(),
        'companies': set(),
        'tools': set(),
        'family': set(),
        'locations': set(),
        'agents': set(),
        'achievements': set()
    }
    
    # Personal relationships
    personal_patterns = [
        r'in a relationship with ([^,\.]+)',
        r'met ([^,\.]+) on',
        r'dating ([^,\.]+)',
        r'partner ([^,\.]+)',
        r'with ([^,\.]+) Hudson'
    ]
    
    for pattern in personal_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            relationships['personal'].add(f"in relationship with {match.strip()}")
    
    # Family relationships
    family_patterns = [
        r'family.*includes ([^,\.]+)',
        r'children,? ([^,\.]+)',
        r'brother ([^,\.]+)',
        r'([^,\.]+) de Guzman'
    ]
    
    for pattern in family_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            relationships['family'].add(f"family member: {match.strip()}")
    
    # Professional relationships
    work_patterns = [
        r'founder of ([^,\.]+)',
        r'worked with companies such as ([^,\.]+)',
        r'worked with ([^,\.]+)',
        r'based in ([^,\.]+)',
        r'specializing in ([^,\.]+)',
        r'expertise in ([^,\.]+)'
    ]
    
    for pattern in work_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if 'founder of' in pattern:
                relationships['companies'].add(f"founder of {match.strip()}")
            elif 'based in' in pattern:
                relationships['locations'].add(f"based in {match.strip()}")
            else:
                relationships['professional'].add(match.strip())
    
    # Skills and expertise
    skill_patterns = [
        r'advanced skills in ([^,\.]+)',
        r'proficient in ([^,\.]+)',
        r'expertise.*in ([^,\.]+)',
        r'focusing on ([^,\.]+)',
        r'specializing in ([^,\.]+)'
    ]
    
    for pattern in skill_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            relationships['skills'].add(f"skilled in {match.strip()}")
    
    # Projects and tools
    project_patterns = [
        r'projects like ([^,\.]+)',
        r'working on ([^,\.]+)',
        r'involved in ([^,\.]+)',
        r'tools.*including ([^,\.]+)',
        r'using ([^,\.]+) for'
    ]
    
    for pattern in project_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if 'tool' in pattern.lower():
                relationships['tools'].add(f"uses {match.strip()}")
            else:
                relationships['projects'].add(f"works on {match.strip()}")
    
    # Agents
    agent_patterns = [
        r'Agent ([^,\.]+)',
        r'agent ([^,\.]+)',
        r'agents.*including ([^,\.]+)',
        r'managing.*agents.*([^,\.]+)'
    ]
    
    for pattern in agent_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            relationships['agents'].add(f"manages agent {match.strip()}")
    
    return relationships

def display_relationships(relationships):
    """Display organized relationships"""
    print("\n" + "="*60)
    print("EMMANUEL'S RELATIONSHIPS & CONNECTIONS")
    print("="*60)
    
    for category, relations in relationships.items():
        if relations:
            print(f"\n🔗 {category.upper()} ({len(relations)} connections):")
            for relation in sorted(relations):
                print(f"   • {relation}")
    
    print("\n" + "="*60)

def search_specific_entities():
    """Search for specific entities that might be connected to Emmanuel"""
    print("\n=== Searching for Connected Entities ===")
    
    connected_entities = [
        "Holly Hudson", "Holly", 
        "Oculair Media", "Oculair",
        "Meridian", "agent Meridian",
        "Charlie", "Oliver", "Joshua", "Josh",
        "Toronto", "Matrix", "Letta"
    ]
    
    connections = {}
    
    for entity_name in connected_entities:
        print(f"\nSearching for: {entity_name}")
        
        search_url = f"{GRAPHITI_API_URL}/search/nodes"
        payload = {
            "query": entity_name,
            "max_nodes": 5,
            "group_ids": []
        }
        
        try:
            response = requests.post(search_url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                nodes = result.get('nodes', [])
                
                for node in nodes:
                    name = node.get('name', '')
                    summary = node.get('summary', '')
                    
                    # Check if summary mentions Emmanuel
                    if 'emmanuel' in summary.lower():
                        if entity_name not in connections:
                            connections[entity_name] = []
                        
                        connections[entity_name].append({
                            'name': name,
                            'uuid': node.get('uuid'),
                            'summary_snippet': summary[:200] + "..." if len(summary) > 200 else summary
                        })
                        
                        print(f"  ✅ Found connection: {name}")
                    else:
                        print(f"  • Found entity: {name} (no Emmanuel connection)")
                        
        except Exception as e:
            print(f"  Error searching {entity_name}: {e}")
    
    return connections

if __name__ == "__main__":
    # Extract relationships from Emmanuel summaries
    relationships = extract_relationships_from_summaries()
    
    # Search for connected entities
    connections = search_specific_entities()
    
    if connections:
        print(f"\n🔍 FOUND {len(connections)} CONNECTED ENTITIES:")
        for entity, details in connections.items():
            print(f"\n{entity}:")
            for detail in details:
                print(f"  • {detail['name']} ({detail['uuid']})")
                print(f"    {detail['summary_snippet']}")