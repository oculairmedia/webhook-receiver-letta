#!/usr/bin/env python3
"""
Improved retrieval system with relevance filtering and fallback strategies
"""
import os
import json
from typing import List, Dict, Any, Optional, Tuple
from retrieve_context import generate_context_from_prompt, search_graphiti_nodes
import requests
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Load sentence transformer for semantic similarity
try:
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
except:
    embedder = None
    print("Warning: SentenceTransformer not available. Falling back to keyword matching.")

def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """Calculate semantic similarity between two texts"""
    if embedder is None:
        # Fallback to simple keyword matching
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        return len(words1.intersection(words2)) / len(words1.union(words2))
    
    try:
        embeddings = embedder.encode([text1, text2])
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return float(similarity)
    except:
        return 0.0

def generate_query_variants(original_query: str) -> List[str]:
    """Generate multiple query variants to improve retrieval"""
    variants = [original_query]
    
    # Add domain-specific expansions based on query content
    query_lower = original_query.lower()
    
    if any(term in query_lower for term in ['ai', 'artificial intelligence', 'machine learning']):
        variants.extend([
            f"{original_query} artificial intelligence machine learning",
            f"AI machine learning {original_query}",
            f"artificial intelligence {original_query} concepts"
        ])
    
    elif any(term in query_lower for term in ['neural', 'network', 'deep learning']):
        variants.extend([
            f"{original_query} neural networks machine learning",
            f"deep learning {original_query}",
            f"neural networks {original_query} algorithms"
        ])
    
    elif any(term in query_lower for term in ['python', 'programming', 'code']):
        variants.extend([
            f"{original_query} programming language",
            f"Python {original_query} tutorial",
            f"coding {original_query} examples"
        ])
    
    elif any(term in query_lower for term in ['quantum', 'computing', 'computer']):
        variants.extend([
            f"{original_query} quantum computing technology",
            f"quantum {original_query} principles",
            f"computing {original_query} science"
        ])
    
    return variants

def filter_by_relevance(entities: List[Dict[str, Any]], query: str, min_threshold: float = 0.2) -> List[Dict[str, Any]]:
    """Filter entities by semantic relevance to the query"""
    filtered_entities = []
    
    for entity in entities:
        # Calculate relevance based on name and summary
        name_similarity = calculate_semantic_similarity(query, entity.get('name', ''))
        summary_similarity = calculate_semantic_similarity(query, entity.get('summary', ''))
        
        # Use the higher of the two similarities
        relevance_score = max(name_similarity, summary_similarity)
        
        if relevance_score >= min_threshold:
            entity['relevance_score'] = relevance_score
            filtered_entities.append(entity)
        else:
            print(f"Filtered out low relevance entity: {entity.get('name', 'Unknown')} (score: {relevance_score:.3f})")
    
    # Sort by relevance score
    return sorted(filtered_entities, key=lambda x: x.get('relevance_score', 0), reverse=True)

def external_knowledge_fallback(query: str) -> str:
    """Fallback to external knowledge when internal results are poor"""
    # This could integrate with Wikipedia, educational APIs, etc.
    # For now, return a helpful message
    return f"Note: Limited relevant information found in knowledge graph for '{query}'. Consider consulting external sources for comprehensive information."

def improved_context_retrieval(
    messages,
    graphiti_url: str,
    max_nodes: int = 5,
    max_facts: int = 15,
    group_ids: Optional[List[str]] = None,
    relevance_threshold: float = 0.2,
    max_results: int = 3
) -> str:
    """
    Improved context retrieval with relevance filtering and fallback strategies
    """
    
    # Extract the primary query
    if isinstance(messages, str):
        primary_query = messages
    elif isinstance(messages, list) and messages:
        primary_query = messages[-1].get('content', '')
    else:
        return "No valid query provided."
    
    print(f"🔍 Improved retrieval for query: {primary_query}")
    print(f"Settings: max_nodes={max_nodes}, threshold={relevance_threshold}")
    
    # Configure session
    session = requests.Session()
    search_group_ids = group_ids if group_ids is not None else []
    
    # Generate query variants
    query_variants = generate_query_variants(primary_query)
    print(f"📝 Generated {len(query_variants)} query variants")
    
    # Collect results from all variants
    all_entities = []
    entities_seen = set()  # Track UUIDs to avoid duplicates
    
    for i, variant in enumerate(query_variants):
        print(f"  Searching variant {i+1}: {variant}")
        
        try:
            entities = search_graphiti_nodes(
                session=session,
                base_url=graphiti_url,
                query=variant,
                group_ids=search_group_ids,
                max_nodes=max_nodes
            )
            
            # Add new entities (avoid duplicates by UUID)
            for entity in entities:
                uuid = entity.get('uuid')
                if uuid and uuid not in entities_seen:
                    all_entities.append(entity)
                    entities_seen.add(uuid)
            
        except Exception as e:
            print(f"  Error searching variant '{variant}': {e}")
            continue
    
    print(f"📊 Found {len(all_entities)} total unique entities before filtering")
    
    # Filter by relevance
    relevant_entities = filter_by_relevance(all_entities, primary_query, relevance_threshold)
    
    print(f"✅ {len(relevant_entities)} entities passed relevance threshold")
    
    # If we have very few relevant results, lower the threshold
    if len(relevant_entities) < 2 and relevance_threshold > 0.1:
        print("🔄 Lowering threshold for second pass...")
        relevant_entities = filter_by_relevance(all_entities, primary_query, 0.1)
        print(f"✅ Second pass found {len(relevant_entities)} entities")
    
    # Limit to max_results best entities
    final_entities = relevant_entities[:max_results]
    
    if not final_entities:
        fallback_message = external_knowledge_fallback(primary_query)
        return fallback_message
    
    # Format the results
    context_parts = ["Relevant Entities from Knowledge Graph:"]
    
    for i, entity in enumerate(final_entities):
        context_parts.append(f"  Entity {i+1}: {entity.get('name', 'Unknown Entity')}")
        context_parts.append(f"    Summary: {entity.get('summary', 'No summary available.')}")
        context_parts.append(f"    Type: {', '.join(entity.get('labels', ['Unknown']))}")
        context_parts.append(f"    Relevance Score: {entity.get('relevance_score', 0):.3f}")
        if entity.get('uuid'):
            context_parts.append(f"    UUID: {entity.get('uuid')}")
    
    context_parts.append("-" * 40)
    
    # Add quality metrics
    avg_relevance = sum(e.get('relevance_score', 0) for e in final_entities) / len(final_entities)
    context_parts.append(f"Retrieval Quality: {len(final_entities)} entities, avg relevance: {avg_relevance:.3f}")
    
    session.close()
    return "\n".join(context_parts)

def test_improved_retrieval():
    """Test the improved retrieval system"""
    test_queries = [
        "What is artificial intelligence?",
        "How do neural networks learn?", 
        "Tell me about Python programming",
        "What are the benefits of renewable energy?",
        "Explain quantum computing"
    ]
    
    print("🧪 Testing Improved Retrieval System")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        print("-" * 40)
        
        result = improved_context_retrieval(
            messages=query,
            graphiti_url="http://192.168.50.90:8001/api",
            max_nodes=8,  # Search more broadly
            max_facts=15,
            relevance_threshold=0.2,
            max_results=3  # Return fewer, better results
        )
        
        print(result)
        print("\n" + "=" * 60)

if __name__ == "__main__":
    test_improved_retrieval()