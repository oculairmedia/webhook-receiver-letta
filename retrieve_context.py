#!/usr/bin/env python3
"""
Retrieves relevant context from Graphiti based on a user prompt.
This context can then be injected into an LLM.
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin
import re # For UUID check

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import logging
from llm_clients.cerebras_qwen_client import CerebrasQwenClient, CerebrasError
# Default configuration
DEFAULT_GRAPHITI_URL = "http://192.168.50.90:8001"
DEFAULT_MAX_NODES = 8  # Increased to return more entities
DEFAULT_MAX_FACTS = 20 # Increased to show more relationship details

def make_request(session: requests.Session, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function to make a POST request and handle common errors."""
    try:
        response = session.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        return {"error": f"HTTP error occurred: {http_err} - {response.text}"}
    except requests.exceptions.ConnectionError as conn_err:
        return {"error": f"Connection error occurred: {conn_err}"}
    except requests.exceptions.Timeout as timeout_err:
        return {"error": f"Timeout error occurred: {timeout_err}"}
    except requests.exceptions.RequestException as req_err:
        return {"error": f"An unexpected error occurred with the request: {req_err}"}
    except json.JSONDecodeError:
        return {"error": "Failed to decode JSON response from Graphiti."}

def get_node_details_by_uuid(
    session: requests.Session,
    base_url: str,
    node_uuid: str,
    # group_ids are not strictly needed if UUID is globally unique for /search/nodes,
    # but search_graphiti_nodes helper takes it. Default to [] for all groups.
    group_ids: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """
    Attempts to retrieve details for a single node by its UUID
    by using the existing search_graphiti_nodes helper function,
    treating the UUID as a query term.
    """
    if not node_uuid:
        print("Node details lookup: No UUID provided to get_node_details_by_uuid.", file=sys.stderr)
        return None
    
    search_groups = group_ids if group_ids is not None else []
    
    print(f"Node details lookup: Attempting to find node with UUID '{node_uuid}' via search_graphiti_nodes (treating UUID as query).", file=sys.stderr)
    nodes_found = search_graphiti_nodes( # This is the helper function in retrieve_context.py
        session=session,
        base_url=base_url,
        query=node_uuid, # Using UUID as the search query term
        group_ids=search_groups,
        max_nodes=1 # We expect/hope for one primary result
    )
    
    if nodes_found:
        # The search_graphiti_nodes might return a node that matched the UUID string
        # in its text, not necessarily an exact UUID match on the node's own UUID.
        # We will return the first node found by this query.
        # The calling function (get_display_name_for_node) will then decide
        # if the 'name' or 'summary' of this found node is usable.
        found_node_data = nodes_found[0]
        actual_found_uuid = found_node_data.get("uuid")
        if actual_found_uuid != node_uuid:
            print(f"Node details lookup: Queried for UUID '{node_uuid}', but search_graphiti_nodes returned node with UUID '{actual_found_uuid}'. Using this returned node's data.", file=sys.stderr)
        else:
            print(f"Node details lookup: Successfully found node with UUID '{node_uuid}' via search_graphiti_nodes.", file=sys.stderr)
        return found_node_data
    else:
        print(f"Node details lookup: No node found for query '{node_uuid}' via search_graphiti_nodes.", file=sys.stderr)
        return None

def search_graphiti_nodes(
    session: requests.Session,
    base_url: str,
    query: str,
    group_ids: Optional[List[str]] = None,
    max_nodes: int = DEFAULT_MAX_NODES,
) -> List[Dict[str, Any]]:
    """Searches Graphiti for relevant nodes."""
    payload = {
        "query": query,
        "max_nodes": max_nodes,
        "group_ids": group_ids if group_ids is not None else [], # Empty list for all groups
    }
    # Ensure base_url ends with slash for proper joining
    base_url = base_url.rstrip("/") + "/"
    url = urljoin(base_url, "search/nodes")
    result = make_request(session, url, payload)
    if "error" in result or not result.get("nodes"):
        print(f"Node search warning: {result.get('error', 'No nodes found')}", file=sys.stderr)
        return []
    return result.get("nodes", [])

def search_graphiti_facts(
    session: requests.Session,
    base_url: str,
    query: str,
    group_ids: Optional[List[str]] = None,
    max_facts: int = DEFAULT_MAX_FACTS,
) -> List[Dict[str, Any]]:
    """Searches Graphiti for relevant facts."""
    payload = {
        "query": query,
        "max_facts": max_facts,
        "group_ids": group_ids if group_ids is not None else [], # Empty list for all groups
    }
    # Ensure base_url ends with slash for proper joining
    base_url = base_url.rstrip("/") + "/"
    url = urljoin(base_url, "search/facts")
    result = make_request(session, url, payload)
    if "error" in result or not result.get("facts"):
        print(f"Fact search warning: {result.get('error', 'No facts found')}", file=sys.stderr)
        return []
    return result.get("facts", [])

def format_retrieved_info(
    session: requests.Session,
    base_url: str,
    nodes: List[Dict[str, Any]],
    facts: List[Dict[str, Any]],
    initial_node_cache: Dict[str, Dict[str, Any]] # Pre-populated cache from main search
) -> str:
    """Formats the retrieved nodes and facts into a single string for LLM context."""
    context_parts = []
    from collections import defaultdict

    def is_uuid_like(text: Optional[str]) -> bool:
        if not text or not isinstance(text, str):
            return False
        # Basic UUID check: 36 chars, 4 hyphens in correct places.
        # A full regex `^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$`
        # is more robust but this heuristic might be sufficient.
        if len(text) == 36 and text.count('-') == 4:
            parts = text.split('-')
            if len(parts) == 5 and \
               len(parts[0]) == 8 and \
               len(parts[1]) == 4 and \
               len(parts[2]) == 4 and \
               len(parts[3]) == 4 and \
               len(parts[4]) == 12:
                # Further check if all parts (excluding hyphens) are hex, if needed
                # For now, structure is a strong indicator.
                try: # Check if it's a valid hex number when hyphens are removed
                    int(text.replace('-', ''), 16)
                    return True
                except ValueError:
                    return False # Not a valid hex number
        return False

    def get_display_name_for_node(node_data: Optional[Dict[str, Any]], default_name: str = "Unnamed Entity") -> str:
        if not node_data:
            return default_name
        
        name = node_data.get('name')
        summary = node_data.get('summary')

        # Prefer name if it's good (not None, not empty, not UUID-like)
        if name and isinstance(name, str) and name.strip() and not is_uuid_like(name):
            return name.strip()
        # Else, if summary is good, use it (truncated)
        if summary and isinstance(summary, str) and summary.strip():
            return (summary[:75] + '...') if len(summary) > 75 else summary.strip()
        # Else, if name exists (even if UUID-like or empty after strip, but not None), use it as last resort before default
        if name and isinstance(name, str) and name.strip():
             return name.strip() # This will display UUID-like names if no better option
        # Else, use the default
        return default_name

    # Initialize cache with nodes already retrieved from the main search
    node_details_cache: Dict[str, Optional[Dict[str, Any]]] = {k: v for k, v in initial_node_cache.items()}

    if nodes: # nodes here are the ones from the main search, already used for initial_node_cache
        context_parts.append("Relevant Entities from Knowledge Graph:")
        # Group nodes by their best display name for the "Relevant Entities" section
        # This might lead to multiple entities being listed under one "display name" if their actual names are UUIDs but summaries are similar.
        # Or, more likely, if their actual names are identical.
        nodes_by_display_name = defaultdict(list)
        for node_from_search in nodes:
            # Use get_display_name_for_node for entity listing as well for consistency
            # The default for 'Unknown Entity' here is if node_from_search itself is problematic.
            # If node_from_search.get('name') is None, get_display_name_for_node will handle it.
            best_name_for_entity = get_display_name_for_node(node_from_search, node_from_search.get('name', 'Unknown Entity'))
            nodes_by_display_name[best_name_for_entity].append(node_from_search)

        entity_counter = 0
        # Iterate through the display names we've decided on
        for display_name_key, actual_nodes_grouped in nodes_by_display_name.items():
            entity_counter += 1
            context_parts.append(f"  Entity {entity_counter}: {display_name_key}") # Display the best name

            if len(actual_nodes_grouped) == 1:
                node = actual_nodes_grouped[0]
                # If the display_name_key was from summary, and original name was UUID-like, show original name too
                original_name_field = node.get('name')
                if display_name_key != original_name_field and is_uuid_like(original_name_field) :
                    context_parts.append(f"    Original Name Field (UUID-like): {original_name_field}")
                context_parts.append(f"    Summary: {node.get('summary', 'No summary available.')}")
                context_parts.append(f"    Type: {', '.join(node.get('labels', ['Unknown']))}")
                if node.get('group_id'):
                    context_parts.append(f"    Group ID: {node.get('group_id')}")
                if node.get('uuid'):
                    context_parts.append(f"    UUID: {node.get('uuid')}")
            else:
                context_parts.append(f"    (Multiple entities share this display name '{display_name_key}')")
                for i, node_instance in enumerate(actual_nodes_grouped):
                    context_parts.append(f"      Instance {i+1} (UUID: {node_instance.get('uuid', 'N/A')}):")
                    context_parts.append(f"        Name Field: {node_instance.get('name', 'N/A')}") # Show actual name field
                    context_parts.append(f"        Summary: {node_instance.get('summary', 'No summary available.')}")
                    context_parts.append(f"        Type: {', '.join(node_instance.get('labels', ['Unknown']))}")
                    if node_instance.get('group_id'):
                        context_parts.append(f"        Group ID: {node_instance.get('group_id')}")
        context_parts.append("-" * 20)

    # if facts:
    #     context_parts.append("Relevant Facts from Knowledge Graph:")
    #     for i, fact in enumerate(facts):
    #         context_parts.append(f"  Fact {i+1}:")
            
    #         relationship = fact.get('relationship_type', 'RELATES_TO')
            
    #         source_name_from_fact = fact.get('source_name') # Name from the edge data itself
    #         target_name_from_fact = fact.get('target_name') # Name from the edge data itself
    #         source_uuid = fact.get('source_uuid')
    #         target_uuid = fact.get('target_uuid')

    #         # Determine display name for source node
    #         display_source_name = "Unnamed Entity" # Default
    #         source_node_data_for_display = None # To hold data of the source node
    #         if source_uuid: # If there's a UUID, try to get its details
    #             if source_uuid not in node_details_cache:
    #                 # Attempt to fetch only if not already in cache (e.g. from initial_node_cache)
    #                 node_details_cache[source_uuid] = get_node_details_by_uuid(session, base_url, source_uuid)
    #             source_node_data_for_display = node_details_cache.get(source_uuid)
            
    #         # Logic:
    #         # 1. If fact itself has a good source_name, use it.
    #         # 2. Else, use display logic on looked-up/cached source_node_data.
    #         # 3. Else, default to "Unnamed Entity".
    #         # Use the correctly assigned variable: source_name_from_fact
    #         if source_name_from_fact and isinstance(source_name_from_fact, str) and source_name_from_fact.strip() and not is_uuid_like(source_name_from_fact):
    #             display_source_name = source_name_from_fact.strip()
    #         elif source_node_data_for_display: # If name from fact is not good/present, try looked-up data
    #              display_source_name = get_display_name_for_node(source_node_data_for_display)
    #         # else display_source_name remains "Unnamed Entity" (its initialized value)

    #         # Determine display name for target node (similar logic)
    #         display_target_name = "Unnamed Entity" # Default
    #         target_node_data_for_display = None # Will hold data of the target node if found by UUID
    #         if target_uuid:
    #             if target_uuid not in node_details_cache:
    #                 node_details_cache[target_uuid] = get_node_details_by_uuid(session, base_url, target_uuid)
    #             target_node_data_for_display = node_details_cache.get(target_uuid)

    #         # Use the correctly assigned variable: target_name_from_fact
    #         if target_name_from_fact and isinstance(target_name_from_fact, str) and target_name_from_fact.strip() and not is_uuid_like(target_name_from_fact):
    #             display_target_name = target_name_from_fact.strip()
    #         elif target_node_data_for_display: # If name from fact is not good/present, try looked-up data
    #             display_target_name = get_display_name_for_node(target_node_data_for_display)
    #         # else display_target_name remains "Unnamed Entity"
            
    #         fact_sentence = f"    {display_source_name} {relationship} {display_target_name}."
    #         context_parts.append(fact_sentence)

    #         if source_uuid or target_uuid:
    #             uuid_details = []
    #             if source_uuid:
    #                 uuid_details.append(f"Source UUID: {source_uuid}")
    #             if target_uuid:
    #                 uuid_details.append(f"Target UUID: {target_uuid}")
    #             if uuid_details:
    #                 context_parts.append(f"      ({', '.join(uuid_details)})")
            
    #         edge_name_val = fact.get('name')
    #         fact_detail_val = fact.get('fact')
            
    #         additional_details_to_show = []
    #         if edge_name_val and isinstance(edge_name_val, str) and edge_name_val.strip() and edge_name_val.lower() != relationship.lower():
    #             additional_details_to_show.append(f"Edge Label: {edge_name_val.strip()}")

    #         if fact_detail_val and isinstance(fact_detail_val, str) and fact_detail_val.strip():
    #             additional_details_to_show.append(f"Details: {fact_detail_val.strip()}")

    #         if additional_details_to_show:
    #             for detail_line in additional_details_to_show:
    #                  context_parts.append(f"      {detail_line}")

    #         if fact.get('group_id'):
    #             context_parts.append(f"      Group ID: {fact.get('group_id')}")
            
    #         attributes = fact.get('attributes', {})
    #         if attributes:
    #             context_parts.append("      Attributes:")
    #             for key, value in attributes.items():
    #                 context_parts.append(f"        {key}: {value}")
            
    #         if i < len(facts) - 1:
    #             context_parts.append("    ---")
    #     context_parts.append("-" * 20)

    if not context_parts:
        return "No relevant information found in the knowledge graph for the given prompt."

    return "\n".join(context_parts)

# Weighting configuration for messages. These can be overridden by environment variables.
# The weights determine the proportion of max_nodes/max_facts allocated to each message tier.
DEFAULT_WEIGHT_LAST_MESSAGE = 0.6
DEFAULT_WEIGHT_PREVIOUS_ASSISTANT_MESSAGE = 0.25
DEFAULT_WEIGHT_PRIOR_USER_MESSAGE = 0.15

# Environment variable names
ENV_WEIGHT_LAST = "GRAPHITI_WEIGHT_LAST_MESSAGE"
ENV_WEIGHT_PREV_ASSISTANT = "GRAPHITI_WEIGHT_PREVIOUS_ASSISTANT_MESSAGE"
ENV_WEIGHT_PRIOR_USER = "GRAPHITI_WEIGHT_PRIOR_USER_MESSAGE"


def get_float_env_var(name: str, default: float) -> float:
    """Helper to get float environment variable."""
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        print(f"Warning: Invalid value for env var {name}. Using default: {default}", file=sys.stderr)
        return default

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

def generate_context_from_prompt(
    messages: Union[str, List[Dict[str, Any]]], # Can be a single prompt string or a list of message dicts
    graphiti_url: str,
    max_nodes: int,
    max_facts: int,
    group_ids: Optional[List[str]],
) -> str:
    """
    Generates a context string from Graphiti based on the user prompt(s) and search parameters.
    If multiple messages are provided, context is retrieved for each message tier
    (last user, previous assistant, prior user) based on configured weights.
    """
    # Configure session with retries
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # group_ids for search functions should be [] if None, to search all groups
    search_group_ids = group_ids if group_ids is not None else []

    all_retrieved_nodes: List[Dict[str, Any]] = []
    all_retrieved_facts: List[Dict[str, Any]] = []

    # Determine queries and weights
    queries_with_weights = []

    weight_last = get_float_env_var(ENV_WEIGHT_LAST, DEFAULT_WEIGHT_LAST_MESSAGE)
    weight_prev_assistant = get_float_env_var(ENV_WEIGHT_PREV_ASSISTANT, DEFAULT_WEIGHT_PREVIOUS_ASSISTANT_MESSAGE)
    weight_prior_user = get_float_env_var(ENV_WEIGHT_PRIOR_USER, DEFAULT_WEIGHT_PRIOR_USER_MESSAGE)

    if isinstance(messages, str): # Single prompt (backward compatibility)
        # For a single prompt, it gets full weight.
        queries_with_weights.append({"query": messages, "weight": 1.0, "source": "direct_prompt"})
    elif isinstance(messages, list) and messages:
        # Collect potential queries with their original weights, filtering out blank content
        potential_queries = []
        
        # Last message (typically user)
        last_message_content = extract_text_from_content(messages[-1].get("content", "")).strip()
        if last_message_content:
            potential_queries.append({"query": last_message_content, "original_weight": weight_last, "source": "last_message"})

        # Previous message (typically assistant) if available
        if len(messages) > 1:
            prev_assistant_content = extract_text_from_content(messages[-2].get("content", "")).strip()
            if prev_assistant_content:
                 potential_queries.append({"query": prev_assistant_content, "original_weight": weight_prev_assistant, "source": "prev_assistant_message"})
        
        # Prior user message if available
        if len(messages) > 2:
            prior_user_content = extract_text_from_content(messages[-3].get("content", "")).strip()
            if prior_user_content:
                potential_queries.append({"query": prior_user_content, "original_weight": weight_prior_user, "source": "prior_user_message"})
        
        if not potential_queries:
             session.close()
             return "No valid (non-blank) message content provided to search."

        # Re-normalize weights for the valid queries
        total_original_weight = sum(q["original_weight"] for q in potential_queries)

        if total_original_weight > 0.00001:  # Avoid division by zero if all weights are zero
            for q in potential_queries:
                q["weight"] = q["original_weight"] / total_original_weight
                # queries_with_weights.append({"query": q["query"], "weight": q["original_weight"] / total_original_weight, "source": q["source"]})
            queries_with_weights.extend(potential_queries) # Add queries with normalized weights
        elif potential_queries: # All original weights were zero, but there are queries - distribute equally
            equal_weight = 1.0 / len(potential_queries)
            for q in potential_queries:
                q["weight"] = equal_weight
            queries_with_weights.extend(potential_queries)
        else: # Should be caught by `if not potential_queries` already
            session.close()
            return "No valid queries to process after filtering and weighting."

        # Clean up original_weight key if it was added temporarily to potential_queries' items
        for q in queries_with_weights:
            if "original_weight" in q:
                del q["original_weight"]

    else: # Invalid input type
        session.close()
        return "Invalid 'messages' input. Must be a string or a list of message dictionaries."

    # Perform searches for each weighted query
    # To ensure the total number of nodes/facts doesn't exceed max_nodes/max_facts due to rounding,
    # we adjust the last tier's allocation.
    
    # Sort queries by weight descending to prioritize higher weighted searches if counts are tight
    # This is not strictly necessary with the current proportional allocation but good practice.
    # queries_with_weights.sort(key=lambda x: x["weight"], reverse=True)

    total_nodes_to_fetch = max_nodes
    total_facts_to_fetch = max_facts
    
    num_queries = len(queries_with_weights)

    for i, qw in enumerate(queries_with_weights):
        current_query = qw["query"]
        current_weight = qw["weight"]
        current_source = qw.get("source", "unknown_source") # Get the source of the query

        # --- Qwen Query Refinement Start ---
        logger = logging.getLogger(__name__) # Ensure logger is initialized

        refined_query = current_query # Default to original if refinement fails
        
        # Check if query refinement is enabled
        query_refinement_enabled = os.environ.get("QUERY_REFINEMENT_ENABLED", "true").lower() in ("true", "1", "yes")
        
        if query_refinement_enabled:
            try:
                # Initialize the CerebrasQwenClient
                # CEREBRAS_API_KEY should be set as an environment variable
                qwen_client = CerebrasQwenClient()
                                         
                # Determine the actual conversation history for Qwen based on the source of current_query
                qwen_actual_history_for_refinement = []
                if isinstance(messages, list) and messages: # messages is the full history
                    if current_source == "last_message" and len(messages) >= 1:
                        # History is all messages before the last one
                        qwen_actual_history_for_refinement = messages[:-1]
                    elif current_source == "prev_assistant_message" and len(messages) >= 2:
                        # History is all messages before the second to last one
                        qwen_actual_history_for_refinement = messages[:-2]
                    elif current_source == "prior_user_message" and len(messages) >= 3:
                        # History is all messages before the third to last one
                        qwen_actual_history_for_refinement = messages[:-3]
                    # If current_source is "direct_prompt" (from a single string message) or unknown,
                    # qwen_actual_history_for_refinement remains empty.

                # Prepare messages for Qwen API
                qwen_messages_for_api = []
                if qwen_actual_history_for_refinement: # qwen_actual_history_for_refinement is already List[Dict]
                    qwen_messages_for_api.extend(qwen_actual_history_for_refinement)
                
                # Construct a system prompt for query refinement
                refinement_prompt_template = (
                    "You are an AI assistant. Your task is to refine and clarify the following user query, "
                    "considering the provided conversation history, to make it more effective for information retrieval "
                    "from a knowledge graph. Correct typos, make vague queries more specific, and if complex, "
                    "you can break it down or structure it. Output *only* the refined query text, nothing else."
                )
                
                # Combine system instructions with the user query
                # Pass the determined qwen_actual_history_for_refinement to the prompt for Qwen's context
                full_user_content_for_refinement = (
                    f"{refinement_prompt_template}\n\n"
                    f"Conversation History (if any):\n{json.dumps(qwen_actual_history_for_refinement, indent=2)}\n\n"
                    f"User Query to refine:\n{current_query}"
                )
                qwen_messages_for_api.append({"role": "user", "content": full_user_content_for_refinement})

                logger.info(f"Original query for Graphiti (source: {current_source}): {current_query}")
                logger.debug(f"Sending to Qwen for refinement. Messages: {json.dumps(qwen_messages_for_api, indent=2)}")

                # Get temperature from environment, with fallback to 0.3
                refinement_temp = float(os.environ.get("QUERY_REFINEMENT_TEMPERATURE", "0.3"))
                qwen_response = qwen_client.generate_chat_completion(messages=qwen_messages_for_api, temperature=refinement_temp)

                if qwen_response and qwen_response.get("content"):
                    refined_query = qwen_response["content"].strip()
                    logger.info(f"Query refined by Qwen: {refined_query}")
                else:
                    logger.warning("Qwen client did not return content for query refinement. Using original query.")
            
            except ValueError as ve: # Handles API key issues from CerebrasQwenClient init
                logger.error(f"Failed to initialize CerebrasQwenClient for query refinement: {ve}. Using original query.")
            except CerebrasError as ce:
                logger.error(f"Cerebras API error during query refinement: {ce}. Using original query.")
            except Exception as e:
                logger.error(f"Unexpected error during query refinement: {e}. Using original query.")
        else:
            logger.info(f"Query refinement disabled. Using original query: {current_query}")
        # --- Qwen Query Refinement End ---
        
        # Calculate proportional nodes/facts for this query
        # For the last query in the list, assign remaining nodes/facts to avoid exceeding total due to rounding
        if i == num_queries - 1:
            num_nodes_for_query = total_nodes_to_fetch
            num_facts_for_query = total_facts_to_fetch
        else:
            num_nodes_for_query = int(round(max_nodes * current_weight))
            num_facts_for_query = int(round(max_facts * current_weight))

        if num_nodes_for_query > 0:
            retrieved_nodes_for_query = search_graphiti_nodes(
                session, graphiti_url, refined_query, search_group_ids, num_nodes_for_query
            )
            all_retrieved_nodes.extend(retrieved_nodes_for_query)
            total_nodes_to_fetch -= len(retrieved_nodes_for_query) # or num_nodes_for_query, depending on desired strictness
            total_nodes_to_fetch = max(0, total_nodes_to_fetch)


        if num_facts_for_query > 0:
            retrieved_facts_for_query = search_graphiti_facts(
                session, graphiti_url, refined_query, search_group_ids, num_facts_for_query
            )
            all_retrieved_facts.extend(retrieved_facts_for_query)
            total_facts_to_fetch -= len(retrieved_facts_for_query) # or num_facts_for_query
            total_facts_to_fetch = max(0, total_facts_to_fetch)
            
        if total_nodes_to_fetch <= 0 and total_facts_to_fetch <= 0 and i < num_queries -1 :
            # Optimization: if we've already fetched max items and there are more queries,
            # we might stop early if strict adherence to proportions isn't critical
            # For now, continue to give each query a chance based on its original proportion.
            pass

    session.close()
    
    # Deduplicate nodes and facts (optional, but good practice)
    # Simple deduplication by UUID for nodes, and a combination of source/target/type for facts
    unique_nodes = {node['uuid']: node for node in all_retrieved_nodes if 'uuid' in node}.values()
    
    unique_facts_keys = set()
    unique_facts_list = []
    for fact in all_retrieved_facts:
        # Create a unique key for each fact to avoid duplicates
        # Using source_uuid, target_uuid, and relationship_type as a composite key
        fact_key_parts = [
            str(fact.get('source_uuid', 'none')),  # Ensure string representation
            str(fact.get('target_uuid', 'none')),  # Ensure string representation
            str(fact.get('relationship_type', 'none'))  # Ensure string representation
        ]
        # Include fact text if it's significant for uniqueness
        # fact_text = fact.get('fact', fact.get('name'))
        # if fact_text:
        #     fact_key_parts.append(fact_text)
        fact_key = tuple(sorted(fact_key_parts)) # Sort to make (a,b,rel) same as (b,a,rel) if symmetric, though facts are directed

        if fact_key not in unique_facts_keys:
            unique_facts_keys.add(fact_key)
            unique_facts_list.append(fact)
            
    # Ensure we don't exceed the original max_nodes and max_facts after deduplication and aggregation
    final_nodes = list(unique_nodes)[:max_nodes]
    final_facts = unique_facts_list[:max_facts]
    
    # Prepare the initial cache from the successfully retrieved and deduplicated nodes
    # This cache will be passed to format_retrieved_info
    initial_node_cache_for_formatting = {node['uuid']: node for node in final_nodes if 'uuid' in node}

    # The session is closed in the calling function (generate_context_from_prompt) after this returns.
    return format_retrieved_info(session, graphiti_url, final_nodes, final_facts, initial_node_cache_for_formatting)

def main():
    parser = argparse.ArgumentParser(description="Retrieve relevant context from Graphiti for an LLM, or test node lookup.")
    
    # Argument for existing functionality
    parser.add_argument(
        "input_data",
        type=str,
        nargs='?', # Make it optional so --test-uuid can be used alone
        default=None, # Default to None if not provided
        help="The user prompt (string) or a JSON string representing a list of message objects e.g., '[{\"role\": \"user\", \"content\": \"Hello\"}]'. Required if not using --test-uuid."
    )
    parser.add_argument(
        "--url",
        type=str,
        default=os.environ.get("GRAPHITI_URL", DEFAULT_GRAPHITI_URL),
        help=f"Graphiti API base URL (default: {DEFAULT_GRAPHITI_URL} or GRAPHITI_URL env var)",
    )
    parser.add_argument(
        "--max-nodes",
        type=int,
        default=DEFAULT_MAX_NODES,
        help=f"Maximum number of nodes to retrieve (default: {DEFAULT_MAX_NODES})",
    )
    parser.add_argument(
        "--max-facts",
        type=int,
        default=DEFAULT_MAX_FACTS,
        help=f"Maximum number of facts to retrieve (default: {DEFAULT_MAX_FACTS})",
    )
    parser.add_argument(
        "--group-ids",
        type=str,
        help="Comma-separated list of group IDs to filter search (e.g., group1,group2). If not provided, searches all groups.",
    )
    parser.add_argument(
        "--test-uuid",
        type=str,
        default=None,
        help="If provided, script will test fetching details for this single UUID and print the result."
    )

    args = parser.parse_args()

    # Session for HTTP requests, created once and passed around
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        if args.test_uuid:
            print(f"--- Testing get_node_details_by_uuid for UUID: {args.test_uuid} ---")
            # get_node_details_by_uuid no longer takes group_ids
            node_details = get_node_details_by_uuid(session, args.url, args.test_uuid)
            if node_details:
                print(json.dumps(node_details, indent=2))
            else:
                print(f"No details returned for UUID: {args.test_uuid}")
            # No 'return' here; let finally execute.
        
        elif args.input_data is None: # Check if not testing UUID and input_data is missing
            parser.error("input_data is required if --test-uuid is not used.")
            # parser.error typically exits, but if it doesn't, finally will still run.
        
        else: # Proceed with existing functionality if not testing UUID and input_data is present
            parsed_group_ids_main: Optional[List[str]] = None # Renamed to avoid clash if block was different
            if args.group_ids:
                parsed_group_ids_main = [gid.strip() for gid in args.group_ids.split(',')]
        
            messages_input_val_main: Union[str, List[Dict[str, Any]]] # Renamed
            try:
                messages_input_val_main = json.loads(args.input_data)
                if not isinstance(messages_input_val_main, list):
                    print("Parsed JSON is not a list, treating input_data as a single prompt string.", file=sys.stderr)
                    messages_input_val_main = args.input_data
            except json.JSONDecodeError:
                messages_input_val_main = args.input_data

            formatted_context = generate_context_from_prompt(
                messages=messages_input_val_main,
                graphiti_url=args.url,
                max_nodes=args.max_nodes,
                max_facts=args.max_facts,
                group_ids=parsed_group_ids_main,
            )
            print(formatted_context)
    finally:
        print("Closing session.", file=sys.stderr) # Added for verbosity
        session.close() # Ensure session is closed

if __name__ == "__main__":
    main()