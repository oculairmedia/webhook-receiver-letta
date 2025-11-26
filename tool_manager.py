import json
import requests
import sys
import os
from typing import List, Dict, Optional, Any # Added for better type hinting

# Retrieve Letta password from environment or use a default
LETTA_PASSWORD = os.environ.get("LETTA_PASSWORD", "lettaSecurePass123")

# Agent registry configuration
AGENT_REGISTRY_URL = os.environ.get("AGENT_REGISTRY_URL", "http://192.168.50.90:8021")

def get_agent_tools(agent_id: str) -> List[str]: # Return type is List of strings (tool IDs)
    """
    Get the list of tools currently attached to an agent.
    Uses port 8283, X-BARE-PASSWORD authentication, and user_id header.
    
    Args:
        agent_id (str): The agent ID to get tools for
        
    Returns:
        List[str]: List of tool IDs attached to the agent, or empty list if error or none found
    """
    if not agent_id:
        print("Cannot get agent tools: No agent_id provided", file=sys.stderr)
        return []
        
    # URL for listing tools attached to an agent (port 8283)
    # Path based on user's screenshot: /v1/agents/{agent_id}/tools
    url = f"http://192.168.50.90:8283/v1/agents/{agent_id}/tools" 
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json", 
        "X-BARE-PASSWORD": f"password {LETTA_PASSWORD}",
        "user_id": agent_id # As per API docs for this endpoint from user
    }
    
    try:
        print(f"Fetching current tools for agent {agent_id} from {url} with X-BARE-PASSWORD and user_id header...", file=sys.stdout)
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Get agent tools (port 8283) response status: {response.status_code}", file=sys.stdout)
        
        if response.status_code != 200:
            print(f"Error getting agent tools from {url}: {response.status_code} - {response.text}", file=sys.stderr)
            return []
            
        result = response.json() # API doc says this is a list of tool objects
        
        tool_ids = []
        if isinstance(result, list):
            for tool_item in result:
                if isinstance(tool_item, dict) and "id" in tool_item:
                    tool_ids.append(tool_item["id"])
        else:
            print(f"Warning: Expected a list of tools from {url}, got {type(result)}", file=sys.stderr)

        print(f"Found {len(tool_ids)} existing tools for agent {agent_id} via {url}: {tool_ids}", file=sys.stdout)
        return tool_ids
        
    except requests.exceptions.RequestException as e:
        print(f"RequestException fetching agent tools from {url}: {str(e)}", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        # Check if response exists before trying to access response.text
        response_text_snippet = "N/A"
        if 'response' in locals() and hasattr(response, 'text'):
            response_text_snippet = response.text[:200]
        print(f"JSONDecodeError fetching agent tools from {url}: {str(e)}. Response text snippet: {response_text_snippet}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Unexpected error fetching agent tools from {url}: {str(e)}", file=sys.stderr)
        return []

# User-provided find_attach_tools function (modified slightly for consistency and robustness)
def find_attach_tools(query: str = None, agent_id: str = None, keep_tools: str = None, 
                        limit: int = 5, min_score: float = 75.0, request_heartbeat: bool = False,
                        return_structured: bool = False):
    """
    Silently manage tools for the agent. Uses port 8020 and no specific auth headers beyond Content-Type.
    
    Args:
        query (str): Your search query - what kind of tool are you looking for?
        agent_id (str): Your agent ID
        keep_tools (str): Comma-separated list of tool IDs to preserve.
                          If None or empty, no tools are explicitly kept (API default behavior).
        limit (int): Maximum number of tools to find (default: 5)
        min_score (float): Minimum match score 0-100 (default: 75.0) - INCREASED for more aggressive filtering
        request_heartbeat (bool): Whether to request an immediate heartbeat (default: False)
        return_structured (bool): If True, return the full API response dict instead of string message
    
    Returns:
        str or dict: Success message (str) or full API response (dict) if return_structured=True
    """
    # URL for attaching tools (port 8020)
    url = "http://192.168.50.90:8020/api/v1/tools/attach"
    # Headers as per user's provided code for this endpoint (no X-BARE-PASSWORD or user_id)
    headers = {"Content-Type": "application/json"} 
    
    # Convert keep_tools string to list of strings.
    # The API endpoint for attach expects "keep_tools" to be a list of tool IDs.
    # Handle "*" wildcard to mean "keep all current agent tools"
    keep_tool_ids_list: List[str] = []
    if keep_tools: # Handles None or empty string
        keep_tool_ids_list = [t.strip() for t in keep_tools.split(',') if t.strip()]
        
        # Expand "*" wildcard to actual tool IDs
        if "*" in keep_tool_ids_list:
            if agent_id:
                print(f"[find_attach_tools] Expanding '*' wildcard for agent {agent_id}")
                current_tool_ids = get_agent_tools(agent_id)
                if current_tool_ids:
                    # Remove "*" and add all current tool IDs
                    keep_tool_ids_list.remove("*")
                    keep_tool_ids_list.extend(current_tool_ids)
                    # Remove duplicates while preserving order
                    seen = set()
                    keep_tool_ids_list = [x for x in keep_tool_ids_list if not (x in seen or seen.add(x))]
                    print(f"[find_attach_tools] Expanded '*' to {len(current_tool_ids)} current tools")
                else:
                    print(f"[find_attach_tools] Warning: '*' specified but no tools found for agent {agent_id}")
                    keep_tool_ids_list.remove("*")
            else:
                print(f"[find_attach_tools] Warning: '*' specified but no agent_id provided, removing wildcard")
                keep_tool_ids_list.remove("*")
    
    payload: Dict[str, Any] = {
        "limit": limit, # Using the passed limit, which has a default in signature
        "min_score": min_score, # Using the passed min_score, which has a default
        "keep_tools": keep_tool_ids_list, 
        "request_heartbeat": request_heartbeat
    }
    
    if query is not None:
        payload["query"] = query
    if agent_id is not None and agent_id.strip() != "":
        payload["agent_id"] = agent_id

    print("Tool attachment payload (to :8020):", file=sys.stdout) 
    print(json.dumps(payload, indent=2), file=sys.stdout)

    response_text_for_error = "" # To store response text for error logging

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response_text_for_error = response.text # Store for potential error logging

        # Try to parse JSON for detailed logging, even if status code indicates error
        try:
            result = response.json()
            print("Full API Response Details (find_attach_tools from :8020):", file=sys.stdout)
            print(json.dumps(result, indent=2), file=sys.stdout)
        except json.JSONDecodeError:
            result = None
            print(f"Warning: Could not decode JSON from attach response. Status: {response.status_code}, Text: {response_text_for_error[:200]}", file=sys.stderr)

        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        
        # If return_structured is True, return the full response dict
        if return_structured and result:
            return result
        
        # If raise_for_status didn't trigger, and we have a result
        if result and result.get("success"):
            details = result.get("details", {})
            successful_attachments = details.get("successful_attachments", [])
            detached_tools = details.get("detached_tools", [])
            preserved_tools = details.get("preserved_tools", [])
            
            success_parts = []
            if successful_attachments:
                tool_names = [a.get("name", a.get("tool_id", "unknown")) for a in successful_attachments]
                success_parts.append(f"Attached {len(successful_attachments)} tools: {', '.join(tool_names)}")
            if detached_tools:
                success_parts.append(f"Detached {len(detached_tools)} tools")
            if preserved_tools: # This comes from the API response
                 success_parts.append(f"Preserved {len(preserved_tools)} tools (confirmed by API)")
            
            if not success_parts:
                return "Tools updated successfully (no specific changes detailed by API)."
            return "Tools updated successfully. " + " | ".join(success_parts)
        elif result: # Result exists but not success
            error_message = result.get("error", result.get("message", f"API reported failure with status {response.status_code}"))
            return f"Error: {error_message}"
        else: # No JSON result (e.g. 204 No Content, or error before JSON parsing)
             return f"Tools updated (HTTP {response.status_code}). No further details in response."


    except requests.exceptions.HTTPError as http_err:
        # error_content_str will be populated from response_text_for_error or result if available
        error_detail_msg = response_text_for_error[:200] # Default to text snippet
        if result: # If JSON was parsed before raise_for_status
            error_detail_msg = json.dumps(result)
        print(f"HTTPError in find_attach_tools (:8020): {str(http_err)} - Response: {error_detail_msg}", file=sys.stderr)
        return f"Error: HTTP {http_err.response.status_code if http_err.response is not None else 'Unknown'} - {error_detail_msg}"
    except requests.exceptions.RequestException as e:
        print(f"RequestException in find_attach_tools (:8020): {str(e)}", file=sys.stderr)
        return f"Error during tool attachment request: {str(e)}"
    except Exception as e: # Catch any other unexpected error
        print(f"Unexpected error in find_attach_tools (:8020): {type(e).__name__} - {str(e)}", file=sys.stderr)
        return f"Error: An unexpected error occurred: {str(e)}"


def find_agents(query: str, limit: int = 10, min_score: float = 0.3) -> str:
    """
    Search for relevant agents in the agent registry based on a query.
    
    Args:
        query (str): Your search query - what kind of agent are you looking for?
        limit (int): Maximum number of agents to return (default: 10)
        min_score (float): Minimum relevance score 0-1 (default: 0.3)
    
    Returns:
        str: Formatted list of agents or error message
    """
    url = f"{AGENT_REGISTRY_URL}/api/v1/agents/search"
    params = {
        "query": query,
        "limit": limit,
        "min_score": min_score
    }
    
    try:
        print(f"Searching for agents with query: '{query}' (limit={limit}, min_score={min_score})", file=sys.stdout)
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        result = response.json()
        agents = result.get("agents", [])
        
        if not agents:
            return f"No relevant agents found for query: '{query}'"
        
        # Format the results
        output_parts = [f"Found {len(agents)} relevant agents:\n"]
        
        for agent in agents:
            agent_id = agent.get("agent_id", "unknown")
            name = agent.get("name", "Unknown Agent")
            description = agent.get("description", "No description")
            score = agent.get("score", 0.0)
            status = agent.get("status", "unknown")
            capabilities = agent.get("capabilities", [])
            
            agent_info = f"\n• {name} (ID: {agent_id})"
            agent_info += f"\n  Status: {status}"
            agent_info += f"\n  Relevance: {score:.2f}"
            agent_info += f"\n  Description: {description[:150]}{'...' if len(description) > 150 else ''}"
            
            if capabilities:
                agent_info += f"\n  Capabilities: {', '.join(capabilities[:3])}"
            
            output_parts.append(agent_info)
        
        output_parts.append("\n\nYou can message these agents using the matrix_agent_message tool with their agent ID.")
        
        return "\n".join(output_parts)
        
    except requests.exceptions.HTTPError as http_err:
        error_msg = f"HTTP {http_err.response.status_code if http_err.response else 'Unknown'}"
        print(f"HTTPError in find_agents: {str(http_err)}", file=sys.stderr)
        return f"Error searching for agents: {error_msg}"
    except requests.exceptions.RequestException as e:
        print(f"RequestException in find_agents: {str(e)}", file=sys.stderr)
        return f"Error during agent search request: {str(e)}"
    except Exception as e:
        print(f"Unexpected error in find_agents: {type(e).__name__} - {str(e)}", file=sys.stderr)
        return f"Error: An unexpected error occurred: {str(e)}"


# Main execution block for CLI
if __name__ == "__main__":
    args_dict: Dict[str, Optional[str]] = {}
    i = 1
    while i < len(sys.argv):
        if sys.argv[i].startswith('--'):
            key = sys.argv[i][2:]
            if i + 1 < len(sys.argv) and not sys.argv[i+1].startswith('--'):
                args_dict[key] = sys.argv[i+1]
                i += 2
            else: 
                args_dict[key] = "true" 
                i += 1
        else:
            i += 1 
    
    query_arg = args_dict.get('query')
    agent_id_arg = args_dict.get('agent_id')
    keep_tools_cli_input = args_dict.get('keep_tools') 
    
    limit_arg = int(args_dict.get('limit', '5'))
    min_score_arg = float(args_dict.get('min_score', '75.0')) # INCREASED default from 50.0 to 75.0
    request_heartbeat_arg = str(args_dict.get('request_heartbeat', 'false')).lower() == 'true'
    
    final_keep_tools_str = "" # This will be the comma-separated string of tool IDs

    if agent_id_arg: 
        if keep_tools_cli_input == "*":
            print(f"CLI: '*' specified for keep_tools with agent_id {agent_id_arg}. Fetching current tools...")
            fetched_tool_ids = get_agent_tools(agent_id_arg)
            if fetched_tool_ids:
                final_keep_tools_str = ",".join(fetched_tool_ids)
                print(f"CLI: Using fetched tools for keep_tools: {final_keep_tools_str}")
            else:
                print("CLI: No tools found for agent or error fetching. Proceeding with empty keep_tools.")
        elif keep_tools_cli_input: # If it's not "*" but some other string (already a list of IDs)
            final_keep_tools_str = keep_tools_cli_input
            print(f"CLI: Using provided keep_tools string: {final_keep_tools_str}")
        # If keep_tools_cli_input is None or empty, final_keep_tools_str remains ""
    elif keep_tools_cli_input == "*": # "*" without agent_id
        print("CLI: '*' specified for keep_tools, but no agent_id provided. Cannot fetch tools. Proceeding with empty keep_tools.", file=sys.stderr)
    elif keep_tools_cli_input: # Some string without agent_id
        final_keep_tools_str = keep_tools_cli_input # Use as is, might be global tool IDs
        print(f"CLI: Using provided keep_tools string (no agent_id): {final_keep_tools_str}")


    result_message = find_attach_tools(
        query=query_arg,
        agent_id=agent_id_arg,
        keep_tools=final_keep_tools_str, 
        limit=limit_arg,
        min_score=min_score_arg,
        request_heartbeat=request_heartbeat_arg
    )
    print(result_message)