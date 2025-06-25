#!/usr/bin/env python3

import requests
import json
import os
import re
from collections import defaultdict, Counter
from datetime import datetime

GRAPHITI_API_URL = os.environ.get("GRAPHITI_URL", "http://192.168.50.90:8001/api")

def knowledge_graph_analytics():
    """Analyze the overall structure and content of the knowledge graph"""
    print("=" * 80)
    print("🧠 GRAPHITI KNOWLEDGE GRAPH ANALYTICS")
    print("=" * 80)
    
    # Get all nodes with a broad search
    search_url = f"{GRAPHITI_API_URL}/search/nodes"
    payload = {
        "query": "",  # Empty query to get all nodes
        "max_nodes": 500,
        "group_ids": []
    }
    
    try:
        response = requests.post(search_url, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            nodes = result.get('nodes', [])
            
            print(f"📊 Total Entities in Graph: {len(nodes)}")
            
            # Analyze entity types and categories
            analyze_entity_types(nodes)
            analyze_entity_relationships(nodes)
            find_knowledge_clusters(nodes)
            
            return nodes
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return []

def analyze_entity_types(nodes):
    """Categorize entities by type/domain"""
    print(f"\n🏷️  ENTITY CATEGORIES:")
    
    categories = {
        'people': [],
        'companies': [],
        'projects': [],
        'technologies': [],
        'locations': [],
        'agents': [],
        'tools': [],
        'concepts': [],
        'other': []
    }
    
    # Categorization patterns
    patterns = {
        'people': [r'\b(Emmanuel|Holly|Joshua|Josh|Charlie|Oliver)\b', r'\b(person|user|developer|designer)\b'],
        'companies': [r'\b(Media|Company|Inc|Corp|LLC)\b', r'\b(Oculair|Branton|Incontrol|Apollo)\b'],
        'projects': [r'\b(Project|project)\b', r'\b(Letta|Plane|Bookstack|Matrix)\b'],
        'technologies': [r'\b(API|HTTP|MCP|SSH|Docker|Redis)\b', r'\b(technology|framework|protocol)\b'],
        'locations': [r'\b(Toronto|Ontario|Canada|Oakville)\b', r'\b(city|location|based in)\b'],
        'agents': [r'\b(Agent|agent|Meridian)\b', r'\b(AI|assistant|bot)\b'],
        'tools': [r'\b(tool|Tool)\b', r'\b(server|application|software)\b'],
        'concepts': [r'\b(concept|idea|principle|strategy)\b', r'\b(architecture|design|pattern)\b']
    }
    
    for node in nodes:
        name = node.get('name', '')
        summary = node.get('summary', '')
        text = f"{name} {summary}".lower()
        
        categorized = False
        for category, category_patterns in patterns.items():
            if any(re.search(pattern, text, re.IGNORECASE) for pattern in category_patterns):
                categories[category].append(node)
                categorized = True
                break
        
        if not categorized:
            categories['other'].append(node)
    
    for category, entities in categories.items():
        if entities:
            print(f"  {category.upper()}: {len(entities)} entities")
            for entity in entities[:3]:  # Show first 3 examples
                print(f"    • {entity.get('name', 'N/A')}")
            if len(entities) > 3:
                print(f"    ... and {len(entities) - 3} more")

def analyze_entity_relationships(nodes):
    """Find relationship patterns and network connections"""
    print(f"\n🔗 RELATIONSHIP NETWORK ANALYSIS:")
    
    # Extract mention patterns
    mentions = defaultdict(list)
    
    for node in nodes:
        name = node.get('name', '')
        summary = node.get('summary', '')
        
        # Find other entity names mentioned in this summary
        for other_node in nodes:
            other_name = other_node.get('name', '')
            if other_name != name and other_name.lower() in summary.lower() and len(other_name) > 2:
                mentions[name].append(other_name)
    
    # Find most connected entities
    connection_counts = {name: len(connections) for name, connections in mentions.items()}
    top_connected = sorted(connection_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    print(f"  Most Connected Entities:")
    for entity, count in top_connected:
        print(f"    • {entity}: {count} connections")
        if mentions[entity]:
            print(f"      Connected to: {', '.join(mentions[entity][:5])}{'...' if len(mentions[entity]) > 5 else ''}")

def find_knowledge_clusters(nodes):
    """Identify knowledge clusters and domains"""
    print(f"\n🌐 KNOWLEDGE CLUSTERS:")
    
    # Group by common themes
    clusters = {
        'AI & Agents': [],
        'Technical Infrastructure': [],
        'Personal & Family': [],
        'Business & Professional': [],
        'Projects & Development': []
    }
    
    cluster_keywords = {
        'AI & Agents': ['agent', 'ai', 'meridian', 'assistant', 'bot', 'letta'],
        'Technical Infrastructure': ['mcp', 'server', 'docker', 'ssh', 'api', 'transport', 'redis'],
        'Personal & Family': ['holly', 'emmanuel', 'joshua', 'charlie', 'oliver', 'family', 'relationship'],
        'Business & Professional': ['oculair', 'media', 'design', 'animation', 'photography', 'client'],
        'Projects & Development': ['project', 'development', 'github', 'repository', 'implementation']
    }
    
    for node in nodes:
        name = node.get('name', '')
        summary = node.get('summary', '')
        text = f"{name} {summary}".lower()
        
        best_cluster = None
        max_matches = 0
        
        for cluster, keywords in cluster_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in text)
            if matches > max_matches:
                max_matches = matches
                best_cluster = cluster
        
        if best_cluster and max_matches > 0:
            clusters[best_cluster].append((node, max_matches))
    
    for cluster, entities in clusters.items():
        if entities:
            print(f"  {cluster}: {len(entities)} entities")
            # Sort by relevance score
            entities.sort(key=lambda x: x[1], reverse=True)
            for entity, score in entities[:3]:
                print(f"    • {entity.get('name', 'N/A')} (relevance: {score})")

def semantic_search_examples():
    """Demonstrate advanced semantic search capabilities"""
    print(f"\n🔍 SEMANTIC SEARCH CAPABILITIES:")
    
    search_queries = [
        ("Who works with Emmanuel?", "emmanuel collaboration work"),
        ("What AI projects exist?", "ai agent project development"),
        ("Technical infrastructure components", "server infrastructure technology"),
        ("Family relationships", "family personal relationship"),
        ("Business and clients", "business client company professional")
    ]
    
    for description, query in search_queries:
        print(f"\n  {description}:")
        
        search_url = f"{GRAPHITI_API_URL}/search/nodes"
        payload = {
            "query": query,
            "max_nodes": 5,
            "group_ids": []
        }
        
        try:
            response = requests.post(search_url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                nodes = result.get('nodes', [])
                
                for node in nodes:
                    name = node.get('name', 'N/A')
                    summary = node.get('summary', '')[:100] + "..." if len(node.get('summary', '')) > 100 else node.get('summary', '')
                    print(f"    • {name}: {summary}")
        except Exception as e:
            print(f"    Error: {e}")

def temporal_analysis():
    """Analyze temporal patterns and recent activities"""
    print(f"\n⏰ TEMPORAL ANALYSIS:")
    
    # Search for recent activities
    recent_keywords = ["recent", "currently", "now", "today", "latest", "ongoing", "active"]
    
    search_url = f"{GRAPHITI_API_URL}/search/nodes"
    
    for keyword in recent_keywords[:3]:  # Limit to avoid too many requests
        payload = {
            "query": keyword,
            "max_nodes": 10,
            "group_ids": []
        }
        
        try:
            response = requests.post(search_url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                nodes = result.get('nodes', [])
                
                if nodes:
                    print(f"\n  Recent activities ({keyword}):")
                    for node in nodes[:3]:
                        name = node.get('name', 'N/A')
                        summary = node.get('summary', '')
                        # Extract recent activity mentions
                        sentences = summary.split('.')
                        recent_sentences = [s.strip() for s in sentences if keyword.lower() in s.lower()]
                        if recent_sentences:
                            print(f"    • {name}: {recent_sentences[0][:150]}...")
        except Exception as e:
            print(f"    Error searching {keyword}: {e}")

def knowledge_gaps_and_opportunities():
    """Identify potential knowledge gaps and expansion opportunities"""
    print(f"\n🎯 KNOWLEDGE EXPANSION OPPORTUNITIES:")
    
    # Common entity types that might be missing
    gap_searches = [
        ("Skills & Technologies", ["python", "javascript", "database", "cloud", "aws"]),
        ("Industry Contacts", ["client", "customer", "partner", "vendor", "supplier"]),
        ("Project Timeline", ["deadline", "milestone", "schedule", "planning", "roadmap"]),
        ("Documentation", ["documentation", "guide", "tutorial", "manual", "wiki"])
    ]
    
    for category, keywords in gap_searches:
        found_entities = []
        
        for keyword in keywords:
            search_url = f"{GRAPHITI_API_URL}/search/nodes"
            payload = {
                "query": keyword,
                "max_nodes": 5,
                "group_ids": []
            }
            
            try:
                response = requests.post(search_url, json=payload, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    nodes = result.get('nodes', [])
                    found_entities.extend([node.get('name', '') for node in nodes])
            except:
                pass
        
        print(f"\n  {category}:")
        if found_entities:
            unique_entities = list(set(found_entities))[:5]
            print(f"    Found: {', '.join(unique_entities)}")
        else:
            print(f"    ⚠️  Limited information found - potential expansion area")

def export_knowledge_summary():
    """Export a comprehensive knowledge summary"""
    print(f"\n📋 KNOWLEDGE GRAPH SUMMARY EXPORT:")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Get comprehensive data
    search_url = f"{GRAPHITI_API_URL}/search/nodes"
    payload = {
        "query": "",
        "max_nodes": 100,
        "group_ids": []
    }
    
    try:
        response = requests.post(search_url, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            nodes = result.get('nodes', [])
            
            # Create summary structure
            summary = {
                "timestamp": timestamp,
                "total_entities": len(nodes),
                "key_people": [],
                "key_projects": [],
                "key_technologies": [],
                "recent_activities": []
            }
            
            # Populate summary categories
            for node in nodes:
                name = node.get('name', '')
                summary_text = node.get('summary', '')
                
                if any(person in name.lower() for person in ['emmanuel', 'holly', 'meridian']):
                    summary["key_people"].append({"name": name, "summary": summary_text[:200] + "..."})
                
                if any(project in summary_text.lower() for project in ['project', 'letta', 'matrix', 'plane']):
                    summary["key_projects"].append({"name": name, "summary": summary_text[:200] + "..."})
                
                if any(tech in summary_text.lower() for tech in ['mcp', 'api', 'server', 'docker']):
                    summary["key_technologies"].append({"name": name, "summary": summary_text[:200] + "..."})
            
            # Limit each category
            for key in ["key_people", "key_projects", "key_technologies"]:
                summary[key] = summary[key][:5]
            
            print(f"  📄 Summary created with {summary['total_entities']} entities")
            print(f"  👥 Key People: {len(summary['key_people'])}")
            print(f"  🚀 Key Projects: {len(summary['key_projects'])}")
            print(f"  🔧 Key Technologies: {len(summary['key_technologies'])}")
            
            # Save to file
            filename = f"graphiti_knowledge_summary_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(summary, f, indent=2)
            
            print(f"  💾 Exported to: {filename}")
            
    except Exception as e:
        print(f"  ❌ Export error: {e}")

def main():
    """Run comprehensive Graphiti knowledge graph analysis"""
    print("🚀 Starting Comprehensive Graphiti Knowledge Graph Analysis...")
    
    # Core analytics
    nodes = knowledge_graph_analytics()
    
    if nodes:
        # Advanced capabilities
        semantic_search_examples()
        temporal_analysis()
        knowledge_gaps_and_opportunities()
        export_knowledge_summary()
        
        # Future possibilities
        print(f"\n🔮 FUTURE POSSIBILITIES:")
        print(f"  • Real-time knowledge graph updates via webhook")
        print(f"  • Graph visualization and network analysis")
        print(f"  • Automated relationship discovery")
        print(f"  • Knowledge graph querying via natural language")
        print(f"  • Cross-entity recommendation engine")
        print(f"  • Temporal knowledge evolution tracking")
        print(f"  • Knowledge graph embeddings for similarity search")
        print(f"  • Automated fact-checking and consistency validation")
    
    print(f"\n✅ Analysis complete!")

if __name__ == "__main__":
    main()