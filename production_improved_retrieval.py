#!/usr/bin/env python3
"""
Production-ready improved retrieval system for webhook integration
"""
import os
from typing import List, Dict, Any, Optional
from retrieve_context import search_graphiti_nodes, format_retrieved_info
import requests

# Try to import sentence transformers, fallback gracefully
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    SEMANTIC_AVAILABLE = True
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
except ImportError:
    SEMANTIC_AVAILABLE = False
    embedder = None
    print("Warning: Semantic similarity not available. Using keyword matching fallback.")

def calculate_relevance_score(query: str, entity: Dict[str, Any]) -> float:
    """Calculate relevance score between query and entity"""
    if not SEMANTIC_AVAILABLE:
        # Fallback to keyword matching
        query_words = set(query.lower().split())
        entity_text = f"{entity.get('name', '')} {entity.get('summary', '')}"
        entity_words = set(entity_text.lower().split())
        if not query_words or not entity_words:
            return 0.0
        return len(query_words.intersection(entity_words)) / len(query_words.union(entity_words))
    
    try:
        # Use semantic similarity
        entity_text = f"{entity.get('name', '')} {entity.get('summary', '')}"
        embeddings = embedder.encode([query, entity_text])
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return float(similarity)
    except Exception:
        return 0.0

def generate_enhanced_queries(original_query: str) -> List[str]:
    """Generate enhanced query variants for better retrieval"""
    queries = [original_query]
    query_lower = original_query.lower()
    
    # Domain-specific expansions
    if any(term in query_lower for term in ['ai', 'artificial intelligence', 'machine learning']):
        queries.append(f"{original_query} artificial intelligence machine learning")
    elif any(term in query_lower for term in ['neural', 'network', 'deep learning']):
        queries.append(f"{original_query} neural networks machine learning")
    elif any(term in query_lower for term in ['python', 'programming', 'code']):
        queries.append(f"{original_query} programming language")
    elif any(term in query_lower for term in ['quantum', 'computing']):
        queries.append(f"{original_query} quantum computing technology")
    
    return queries

def extract_text_from_content(content) -> str:
    """
    Helper function to extract text from message content.
    Handles both string content and list content (like from webhooks).
    """
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        # Extract text from content list (format: [{"type": "text", "text": "..."}])
        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'text':
                text_parts.append(item.get('text', ''))
        return ' '.join(text_parts)
    else:
        return str(content)

def improved_generate_context_from_prompt(
    messages,
    graphiti_url: str,
    max_nodes: int = 8,
    max_facts: int = 20,
    group_ids: Optional[List[str]] = None,
    relevance_threshold: float = 0.20,
    max_results: int = 6
) -> str:
    """
    Enhanced context generation with relevance filtering
    Drop-in replacement for the original generate_context_from_prompt
    """
    
    # Extract primary query
    if isinstance(messages, str):
        primary_query = messages
    elif isinstance(messages, list) and messages:
        content = messages[-1].get('content', '')
        # Handle both string content and list content (like from webhooks)
        if isinstance(content, list):
            # Extract text from content list (format: [{"type": "text", "text": "..."}])
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    text_parts.append(item.get('text', ''))
            primary_query = ' '.join(text_parts)
        else:
            primary_query = str(content)
    else:
        return "No valid query provided."
    
    # Early exit for very short queries
    if len(primary_query.strip()) < 3:
        return "Query too short for meaningful retrieval."
    
    print(f"[IMPROVED_RETRIEVAL] Query: {primary_query}")
    
    # Configure session
    session = requests.Session()
    search_group_ids = group_ids if group_ids is not None else []
    
    # Generate query variants
    query_variants = generate_enhanced_queries(primary_query)
    
    # Collect entities from all variants
    all_entities = []
    entities_seen = set()
    
    for variant in query_variants:
        try:
            entities = search_graphiti_nodes(
                session=session,
                base_url=graphiti_url,
                query=variant,
                group_ids=search_group_ids,
                max_nodes=max_nodes * 3  # Search more broadly, filter later
            )
            
            # Add unique entities
            for entity in entities:
                uuid = entity.get('uuid')
                if uuid and uuid not in entities_seen:
                    all_entities.append(entity)
                    entities_seen.add(uuid)
                    
        except Exception as e:
            print(f"[IMPROVED_RETRIEVAL] Error searching variant '{variant}': {e}")
            continue
    
    if not all_entities:
        session.close()
        return "No relevant information found in the knowledge graph."
    
    # Calculate relevance scores and filter
    relevant_entities = []
    for entity in all_entities:
        relevance_score = calculate_relevance_score(primary_query, entity)
        if relevance_score >= relevance_threshold:
            entity['relevance_score'] = relevance_score
            relevant_entities.append(entity)
    
    # Sort by relevance and limit results
    relevant_entities.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    final_entities = relevant_entities[:max_results]
    
    print(f"[IMPROVED_RETRIEVAL] Found {len(all_entities)} total, {len(relevant_entities)} relevant, returning {len(final_entities)}")
    
    if not final_entities:
        # Try with lower threshold
        print(f"[IMPROVED_RETRIEVAL] No entities above threshold {relevance_threshold}, trying lower threshold")
        for entity in all_entities:
            if not hasattr(entity, 'relevance_score'):
                entity['relevance_score'] = calculate_relevance_score(primary_query, entity)
        
        all_entities.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        final_entities = all_entities[:min(2, len(all_entities))]  # Return at most 2 best entities
        
        if not final_entities:
            session.close()
            return f"Limited relevant information found for '{primary_query}'. Consider consulting additional sources."
    
    # Use the original formatting function but with our filtered entities
    # Create initial cache from our filtered entities
    initial_node_cache = {entity.get('uuid'): entity for entity in final_entities if entity.get('uuid')}
    
    # Format using the existing function
    context = format_retrieved_info(session, graphiti_url, final_entities, [], initial_node_cache)
    
    # Add quality metrics
    if final_entities:
        avg_relevance = sum(e.get('relevance_score', 0) for e in final_entities) / len(final_entities)
        context += f"\n\nRetrieval Quality: {len(final_entities)} entities, avg relevance: {avg_relevance:.3f}"
    
    session.close()
    return context

# For backward compatibility, provide the same interface
def generate_context_from_prompt_enhanced(*args, **kwargs):
    """Enhanced version of generate_context_from_prompt with better relevance"""
    return improved_generate_context_from_prompt(*args, **kwargs)

# Main interface - drop-in replacement for original function
def generate_context_from_prompt(*args, **kwargs):
    """Drop-in replacement for original generate_context_from_prompt with enhanced relevance"""
    return improved_generate_context_from_prompt(*args, **kwargs)

# Import the constants from the original module for compatibility
from retrieve_context import (
    DEFAULT_GRAPHITI_URL,
    DEFAULT_MAX_NODES,
    DEFAULT_MAX_FACTS,
    DEFAULT_WEIGHT_LAST_MESSAGE,
    DEFAULT_WEIGHT_PREVIOUS_ASSISTANT_MESSAGE,
    DEFAULT_WEIGHT_PRIOR_USER_MESSAGE,
    ENV_WEIGHT_LAST,
    ENV_WEIGHT_PREV_ASSISTANT,
    ENV_WEIGHT_PRIOR_USER,
    get_float_env_var
)