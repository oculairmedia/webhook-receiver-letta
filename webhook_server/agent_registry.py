"""
Agent Registry Integration Module

Provides functions to interact with the agent registry service for discovering
and registering agents dynamically based on webhook context.
"""

import os
import requests
from typing import Dict, List, Optional
from datetime import datetime, UTC
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# Agent registry configuration
AGENT_REGISTRY_URL = os.environ.get("AGENT_REGISTRY_URL", "http://192.168.50.90:8021")
DEFAULT_MAX_AGENTS = int(os.environ.get("AGENT_REGISTRY_MAX_AGENTS", "10"))
DEFAULT_MIN_SCORE = float(os.environ.get("AGENT_REGISTRY_MIN_SCORE", "0.3"))

# Letta API configuration for fetching agent details
LETTA_API_URL = os.environ.get("LETTA_API_URL", "https://letta.oculair.ca/v1")
LETTA_API_KEY = os.environ.get("LETTA_PASSWORD")


def get_agent_details_from_letta(agent_id: str) -> Optional[Dict]:
    """
    Fetch agent details from Letta API.
    
    Args:
        agent_id: The agent ID to fetch details for
        
    Returns:
        Dict with agent details or None if error
    """
    try:
        url = f"{LETTA_API_URL}/agents/{agent_id}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if LETTA_API_KEY:
            headers["Authorization"] = f"Bearer {LETTA_API_KEY}"
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[AGENT_REGISTRY] Error fetching agent details: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"[AGENT_REGISTRY] Error fetching agent details: {e}")
        return None


def extract_capabilities_from_system_prompt(system_prompt: str) -> List[str]:
    """
    Extract capability keywords from agent's system prompt.
    
    Args:
        system_prompt: The agent's system prompt text
        
    Returns:
        List of capability keywords
    """
    # Simple keyword extraction - can be enhanced with NLP
    capability_keywords = []
    
    # Look for common capability indicators
    indicators = [
        "expert in", "specialized in", "responsible for",
        "manages", "handles", "coordinates", "analyzes",
        "develops", "maintains", "monitors", "tracks"
    ]
    
    system_lower = system_prompt.lower()
    
    for indicator in indicators:
        if indicator in system_lower:
            # Extract context around the indicator
            idx = system_lower.find(indicator)
            context = system_prompt[idx:idx+100]
            capability_keywords.append(context.strip())
    
    return capability_keywords[:5]  # Limit to top 5


def register_agent(agent_id: str) -> bool:
    """
    Register a new agent with the agent registry service.
    
    Args:
        agent_id: The agent ID to register
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Fetch agent details from Letta
        agent_details = get_agent_details_from_letta(agent_id)
        
        if not agent_details:
            print(f"[AGENT_REGISTRY] Cannot register agent {agent_id}: failed to fetch details")
            return False
        
        # Extract relevant information
        name = agent_details.get("name", f"Agent {agent_id}")
        system_prompt = agent_details.get("system", "")
        description = system_prompt[:500] if system_prompt else "No description available"
        
        # Extract capabilities from system prompt
        capabilities = extract_capabilities_from_system_prompt(system_prompt)
        
        # Prepare registration payload
        payload = {
            "agent_id": agent_id,
            "name": name,
            "description": description,
            "capabilities": capabilities,
            "status": "active",
            "tags": [],
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat()
        }
        
        # Call agent registry service
        url = f"{AGENT_REGISTRY_URL}/api/v1/agents/register"
        headers = {"Content-Type": "application/json"}
        
        print(f"[AGENT_REGISTRY] Registering agent {agent_id} at {url}")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code in [200, 201]:
            print(f"[AGENT_REGISTRY] Successfully registered agent {agent_id}")
            return True
        else:
            print(f"[AGENT_REGISTRY] Failed to register agent: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"[AGENT_REGISTRY] Error registering agent {agent_id}: {e}")
        return False


def query_agent_registry(query: str, limit: int = None, min_score: float = None) -> Dict:
    """
    Query the agent registry for relevant agents based on semantic search.
    
    Args:
        query: The search query (typically the user's message)
        limit: Maximum number of agents to return (default: DEFAULT_MAX_AGENTS)
        min_score: Minimum relevance score 0-1 (default: DEFAULT_MIN_SCORE)
        
    Returns:
        Dict with search results or error information
    """
    if limit is None:
        limit = DEFAULT_MAX_AGENTS
    if min_score is None:
        min_score = DEFAULT_MIN_SCORE
    
    try:
        # Configure session with retry logic
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Query agent registry
        search_url = f"{AGENT_REGISTRY_URL}/api/v1/agents/search"
        params = {
            "query": query,
            "limit": limit,
            "min_score": min_score
        }
        
        print(f"[AGENT_REGISTRY] Searching agents at {search_url} with query: '{query[:100]}...'")
        
        response = session.get(search_url, params=params, timeout=15)
        response.raise_for_status()
        
        results = response.json()
        
        print(f"[AGENT_REGISTRY] Found {len(results.get('agents', []))} relevant agents")
        
        # Clean up session
        session.close()
        
        return {"agents": results.get("agents", []), "success": True}
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Error querying agent registry: {e}"
        print(f"[AGENT_REGISTRY] {error_msg}")
        return {"agents": [], "success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error during agent registry query: {e}"
        print(f"[AGENT_REGISTRY] {error_msg}")
        return {"agents": [], "success": False, "error": error_msg}


def format_agent_context(agent_results: Dict) -> str:
    """
    Format agent search results into a minimal context string for memory block.
    Only includes agent name and ID to minimize token usage.
    
    Args:
        agent_results: Results from query_agent_registry()
        
    Returns:
        Formatted string for memory block
    """
    if not agent_results.get("success"):
        error = agent_results.get("error", "Unknown error")
        return f"Error retrieving available agents: {error}"
    
    agents = agent_results.get("agents", [])
    
    if not agents:
        return "No relevant agents found for the current context."
    
    context_parts = ["Available Agents for Collaboration:\n"]
    
    for agent in agents:
        agent_id = agent.get("agent_id", "unknown")
        name = agent.get("name", "Unknown Agent")
        score = agent.get("score", 0.0)
        
        # Minimal format: just name, ID, and relevance
        agent_entry = f"- {name} ({agent_id}) [relevance: {score:.2f}]"
        context_parts.append(agent_entry)
    
    context_parts.append("\nUse matrix_agent_message tool with agent ID to contact them.")
    
    return "\n".join(context_parts)
