#!/usr/bin/env python3

import requests
import json
import os
import re
from collections import defaultdict, Counter
from datetime import datetime

GRAPHITI_API_URL = os.environ.get("GRAPHITI_URL", "http://192.168.50.90:8001/api")

def get_all_entities():
    """Get entities using known successful search terms"""
    print("📊 GATHERING ENTITIES FROM KNOWLEDGE GRAPH...")
    
    # Known successful search terms
    search_terms = [
        "Emmanuel", "Meridian", "agent", "Letta", "Matrix", 
        "Oculair", "Holly", "project", "MCP", "server",
        "tool", "API", "Docker", "Toronto", "design"
    ]
    
    all_entities = {}
    
    for term in search_terms:
        search_url = f"{GRAPHITI_API_URL}/search/nodes"
        payload = {
            "query": term,
            "max_nodes": 50,
            "group_ids": []
        }
        
        try:
            response = requests.post(search_url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                nodes = result.get('nodes', [])
                
                for node in nodes:
                    uuid = node.get('uuid')
                    if uuid and uuid not in all_entities:
                        all_entities[uuid] = node
                        
                print(f"  '{term}': {len(nodes)} entities found")
        except Exception as e:
            print(f"  Error searching '{term}': {e}")
    
    unique_entities = list(all_entities.values())
    print(f"✅ Total unique entities collected: {len(unique_entities)}")
    return unique_entities

def advanced_analytics_demo(entities):
    """Demonstrate advanced analytics capabilities"""
    print("\n" + "=" * 80)
    print("🧠 ADVANCED GRAPHITI CAPABILITIES DEMONSTRATION")
    print("=" * 80)
    
    # 1. Entity Categorization
    print(f"\n1️⃣ SMART ENTITY CATEGORIZATION:")
    categorize_entities(entities)
    
    # 2. Relationship Network Analysis
    print(f"\n2️⃣ RELATIONSHIP NETWORK MAPPING:")
    analyze_relationships(entities)
    
    # 3. Knowledge Domain Clustering
    print(f"\n3️⃣ KNOWLEDGE DOMAIN CLUSTERING:")
    cluster_knowledge_domains(entities)
    
    # 4. Temporal Analysis
    print(f"\n4️⃣ TEMPORAL ACTIVITY ANALYSIS:")
    analyze_temporal_patterns(entities)
    
    # 5. Semantic Search Examples
    print(f"\n5️⃣ SEMANTIC SEARCH CAPABILITIES:")
    demonstrate_semantic_search()
    
    # 6. Knowledge Graph Applications
    print(f"\n6️⃣ PRACTICAL APPLICATIONS:")
    show_practical_applications()

def categorize_entities(entities):
    """Smart entity categorization"""
    categories = {
        '👤 People': [],
        '🏢 Organizations': [],
        '🚀 Projects': [],
        '🤖 AI Agents': [],
        '🔧 Technologies': [],
        '📍 Locations': [],
        '🔗 Relationships': [],
        '📝 Concepts': []
    }
    
    category_patterns = {
        '👤 People': [r'\b(Emmanuel|Holly|Joshua|Charlie|Oliver)\b', r'\bmultimedia designer\b', r'\bfounder\b'],
        '🏢 Organizations': [r'\b(Oculair Media|Incontrol|Branton|Apollo)\b', r'\bcompany\b', r'\bcorporation\b'],
        '🚀 Projects': [r'\b(Letta|Plane|Bookstack|Matrix|Postizz)\b', r'\bproject\b', r'\bdevelopment\b'],
        '🤖 AI Agents': [r'\b(Agent Meridian|Meridian|agent)\b', r'\bassistant\b', r'\bAI\b'],
        '🔧 Technologies': [r'\b(MCP|API|Docker|Redis|SSH|HTTP)\b', r'\btechnology\b', r'\bserver\b'],
        '📍 Locations': [r'\b(Toronto|Ontario|Canada|Oakville)\b', r'\bcity\b', r'\blocation\b'],
        '🔗 Relationships': [r'\brelationship\b', r'\bpartner\b', r'\bfamily\b'],
        '📝 Concepts': [r'\bconcept\b', r'\bidea\b', r'\bstrategy\b']
    }
    
    for entity in entities:
        name = entity.get('name', '')
        summary = entity.get('summary', '')
        text = f"{name} {summary}".lower()
        
        categorized = False
        for category, patterns in category_patterns.items():
            if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                categories[category].append(entity)
                categorized = True
                break
        
        if not categorized:
            categories['📝 Concepts'].append(entity)
    
    for category, items in categories.items():
        if items:
            print(f"  {category}: {len(items)} entities")
            for item in items[:3]:
                print(f"    • {item.get('name', 'N/A')}")
            if len(items) > 3:
                print(f"    ... and {len(items) - 3} more")

def analyze_relationships(entities):
    """Analyze relationship patterns"""
    mentions = defaultdict(set)
    
    for entity in entities:
        name = entity.get('name', '')
        summary = entity.get('summary', '')
        
        # Find other entities mentioned in this summary
        for other_entity in entities:
            other_name = other_entity.get('name', '')
            if other_name != name and len(other_name) > 3:
                if other_name.lower() in summary.lower():
                    mentions[name].add(other_name)
    
    # Find most connected entities
    connection_counts = {name: len(connections) for name, connections in mentions.items()}
    top_connected = sorted(connection_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    
    print(f"  Most Connected Entities:")
    for entity, count in top_connected:
        if count > 0:
            print(f"    🔗 {entity}: {count} connections")
            connections = list(mentions[entity])[:3]
            print(f"       → {', '.join(connections)}{'...' if len(mentions[entity]) > 3 else ''}")

def cluster_knowledge_domains(entities):
    """Cluster entities by knowledge domains"""
    domains = {
        '🤖 AI & Automation': ['ai', 'agent', 'automation', 'letta', 'meridian', 'assistant'],
        '💻 Technology Stack': ['mcp', 'api', 'server', 'docker', 'redis', 'http', 'ssh'],
        '👨‍👩‍👧‍👦 Personal Life': ['emmanuel', 'holly', 'family', 'relationship', 'joshua', 'charlie', 'oliver'],
        '🎨 Creative Business': ['oculair', 'media', 'design', 'animation', 'photography', 'multimedia'],
        '🏗️ Infrastructure': ['infrastructure', 'deployment', 'production', 'server', 'architecture']
    }
    
    domain_entities = defaultdict(list)
    
    for entity in entities:
        name = entity.get('name', '')
        summary = entity.get('summary', '')
        text = f"{name} {summary}".lower()
        
        best_domain = None
        max_score = 0
        
        for domain, keywords in domains.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > max_score:
                max_score = score
                best_domain = domain
        
        if best_domain and max_score > 0:
            domain_entities[best_domain].append((entity, max_score))
    
    for domain, entities_list in domain_entities.items():
        if entities_list:
            print(f"  {domain}: {len(entities_list)} entities")
            entities_list.sort(key=lambda x: x[1], reverse=True)
            for entity, score in entities_list[:3]:
                print(f"    • {entity.get('name', 'N/A')} (relevance: {score})")

def analyze_temporal_patterns(entities):
    """Analyze temporal patterns in the knowledge graph"""
    temporal_indicators = {
        'Current/Active': ['currently', 'active', 'now', 'ongoing', 'present'],
        'Recent': ['recent', 'recently', 'latest', 'new', 'just'],
        'Past': ['previous', 'former', 'was', 'had', 'completed'],
        'Future/Planning': ['plan', 'future', 'will', 'upcoming', 'next']
    }
    
    temporal_entities = defaultdict(list)
    
    for entity in entities:
        summary = entity.get('summary', '').lower()
        
        for time_category, indicators in temporal_indicators.items():
            score = sum(1 for indicator in indicators if indicator in summary)
            if score > 0:
                temporal_entities[time_category].append((entity, score))
    
    for time_category, entities_list in temporal_entities.items():
        if entities_list:
            print(f"  ⏰ {time_category}: {len(entities_list)} entities")
            entities_list.sort(key=lambda x: x[1], reverse=True)
            for entity, score in entities_list[:2]:
                name = entity.get('name', 'N/A')
                summary = entity.get('summary', '')[:100] + "..."
                print(f"    • {name}: {summary}")

def demonstrate_semantic_search():
    """Show semantic search capabilities with practical queries"""
    search_examples = [
        ("🔍 'Who is working on AI projects?'", "AI agent development"),
        ("🔍 'What technical infrastructure exists?'", "server infrastructure technology"),
        ("🔍 'Show me family and personal connections'", "family personal relationship holly"),
        ("🔍 'What are the current active projects?'", "current project active development"),
        ("🔍 'Find business and professional activities'", "business professional client work")
    ]
    
    for description, query in search_examples:
        print(f"\n  {description}")
        print(f"    Query: '{query}'")
        
        search_url = f"{GRAPHITI_API_URL}/search/nodes"
        payload = {
            "query": query,
            "max_nodes": 3,
            "group_ids": []
        }
        
        try:
            response = requests.post(search_url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                nodes = result.get('nodes', [])
                
                if nodes:
                    print(f"    Results:")
                    for node in nodes:
                        name = node.get('name', 'N/A')
                        summary = node.get('summary', '')[:80] + "..." if len(node.get('summary', '')) > 80 else node.get('summary', '')
                        print(f"      → {name}: {summary}")
                else:
                    print(f"    No results found")
        except Exception as e:
            print(f"    Error: {e}")

def show_practical_applications():
    """Show practical applications of the knowledge graph"""
    applications = [
        {
            "name": "🎯 Smart Context Generation",
            "description": "Generate relevant context for AI agents based on conversation history",
            "example": "When user mentions 'Holly', automatically include relationship context"
        },
        {
            "name": "🔗 Relationship Discovery",
            "description": "Find hidden connections between entities",
            "example": "Discover that Matrix project connects to SMS integration via Meridian agent"
        },
        {
            "name": "📊 Knowledge Analytics",
            "description": "Analyze knowledge patterns and gaps",
            "example": "Identify missing documentation or underexplored project areas"
        },
        {
            "name": "🤖 Agent Memory Enhancement",
            "description": "Provide persistent memory for AI agents",
            "example": "Agent Meridian remembers past conversations and project context"
        },
        {
            "name": "🔍 Intelligent Search",
            "description": "Natural language querying of complex relationships",
            "example": "Find 'all projects Emmanuel worked on with technical challenges'"
        },
        {
            "name": "📈 Trend Analysis",
            "description": "Track knowledge evolution over time",
            "example": "Monitor how project priorities and focus areas change"
        },
        {
            "name": "💡 Recommendation Engine",
            "description": "Suggest relevant connections and next actions",
            "example": "Recommend tools or contacts based on current project needs"
        },
        {
            "name": "🔄 Real-time Updates",
            "description": "Keep knowledge current via webhook integration",
            "example": "Automatically update project status from chat conversations"
        }
    ]
    
    for app in applications:
        print(f"\n  {app['name']}")
        print(f"    {app['description']}")
        print(f"    Example: {app['example']}")

def main():
    """Run the comprehensive demo"""
    print("🚀 EXPLORING ADVANCED GRAPHITI CAPABILITIES")
    print("="*80)
    
    # Get entities
    entities = get_all_entities()
    
    if entities:
        # Run advanced analytics
        advanced_analytics_demo(entities)
        
        # Show future possibilities
        print(f"\n🔮 FUTURE POSSIBILITIES:")
        print(f"  • Graph visualization dashboard")
        print(f"  • Natural language query interface")
        print(f"  • Automated knowledge graph expansion")
        print(f"  • Cross-domain knowledge synthesis")
        print(f"  • Predictive relationship modeling")
        print(f"  • Knowledge graph embeddings for ML")
        print(f"  • Multi-modal knowledge integration")
        print(f"  • Collaborative knowledge building")
        
        print(f"\n✅ Demo complete! Your Graphiti knowledge graph is rich with possibilities!")
    else:
        print("❌ No entities found. Check Graphiti server connection.")

if __name__ == "__main__":
    main()