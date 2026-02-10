#!/usr/bin/env python3
"""
Register the find_agents tool with Letta API.
This creates an MCP tool that agents can use to discover other agents.
"""

import os
import requests
import json

LETTA_API_URL = os.environ.get("LETTA_API_URL", "http://192.168.50.90:8289/v1")
LETTA_PASSWORD = os.environ.get("LETTA_PASSWORD")

def register_find_agents_tool():
    """Register the find_agents tool with Letta."""
    
    tool_definition = {
        "name": "find_agents",
        "tags": ["agent-discovery", "collaboration", "search"],
        "source_type": "python",
        "source_code": """import requests
import os

def find_agents(query: str, limit: int = 10, min_score: float = 0.3) -> str:
    \"\"\"
    Search for relevant agents in the agent registry based on a query.
    
    Args:
        query (str): Your search query - what kind of agent are you looking for?
        limit (int): Maximum number of agents to return (default: 10)
        min_score (float): Minimum relevance score 0-1 (default: 0.3)
    
    Returns:
        str: Formatted list of agents or error message
    \"\"\"
    AGENT_REGISTRY_URL = os.environ.get("AGENT_REGISTRY_URL", "http://192.168.50.90:8021")
    url = f"{AGENT_REGISTRY_URL}/api/v1/agents/search"
    params = {
        "query": query,
        "limit": limit,
        "min_score": min_score
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        result = response.json()
        agents = result.get("agents", [])
        
        if not agents:
            return f"No relevant agents found for query: '{query}'"
        
        # Format the results
        output_parts = [f"Found {len(agents)} relevant agents:\\n"]
        
        for agent in agents:
            agent_id = agent.get("agent_id", "unknown")
            name = agent.get("name", "Unknown Agent")
            description = agent.get("description", "No description")
            score = agent.get("score", 0.0)
            status = agent.get("status", "unknown")
            capabilities = agent.get("capabilities", [])
            
            agent_info = f"\\n• {name} (ID: {agent_id})"
            agent_info += f"\\n  Status: {status}"
            agent_info += f"\\n  Relevance: {score:.2f}"
            agent_info += f"\\n  Description: {description[:150]}{'...' if len(description) > 150 else ''}"
            
            if capabilities:
                agent_info += f"\\n  Capabilities: {', '.join(capabilities[:3])}"
            
            output_parts.append(agent_info)
        
        output_parts.append("\\n\\nYou can message these agents using the matrix_agent_message tool with their agent ID.")
        
        return "\\n".join(output_parts)
        
    except Exception as e:
        return f"Error searching for agents: {str(e)}"
""",
        "json_schema": {
            "name": "find_agents",
            "description": "Search for relevant agents in the agent registry to find collaborators or specialists. Returns a list of agents with their IDs, capabilities, and relevance scores.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query describing what kind of agent you're looking for (e.g., 'machine learning expert', 'database administrator', 'content writer')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of agents to return",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    },
                    "min_score": {
                        "type": "number",
                        "description": "Minimum relevance score (0.0-1.0) for returned agents",
                        "default": 0.3,
                        "minimum": 0.0,
                        "maximum": 1.0
                    }
                },
                "required": ["query"]
            }
        }
    }
    
    url = f"{LETTA_API_URL}/tools"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    if LETTA_PASSWORD:
        headers["Authorization"] = f"Bearer {LETTA_PASSWORD}"
    
    try:
        print(f"Registering find_agents tool with Letta at {url}...")
        response = requests.post(url, json=tool_definition, headers=headers, timeout=30)
        
        if response.status_code in [200, 201]:
            result = response.json()
            tool_id = result.get("id", "unknown")
            print(f"✓ Successfully registered find_agents tool")
            print(f"  Tool ID: {tool_id}")
            print(f"  Tool Name: {result.get('name')}")
            print(f"\nTo attach this tool to an agent, use:")
            print(f"  POST {LETTA_API_URL}/agents/{{agent_id}}/tools")
            print(f"  Body: {{\"tool_id\": \"{tool_id}\"}}")
            return True
        else:
            print(f"✗ Failed to register tool: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error registering tool: {e}")
        return False


if __name__ == "__main__":
    if not LETTA_PASSWORD:
        print("Warning: LETTA_PASSWORD not set in environment")
        print("Using default or no authentication")
    
    success = register_find_agents_tool()
    exit(0 if success else 1)
