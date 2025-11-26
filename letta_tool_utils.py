import os
import requests
import json
from typing import Optional
import sys

# Environment configuration
LETTA_URL = os.environ.get('LETTA_API_URL', 'https://letta.oculair.ca/v1')
# Ensure it's always HTTPS
if LETTA_URL.startswith('http://'):
    LETTA_URL = LETTA_URL.replace('http://', 'https://', 1)
if not LETTA_URL.endswith('/v1'):
    LETTA_URL = LETTA_URL.rstrip('/') + '/v1'

LETTA_API_KEY = os.environ.get('LETTA_PASSWORD')

def get_find_tools_id(agent_id: Optional[str] = None) -> Optional[str]:
    """
    Dynamically query the Letta API to find the tool ID for find_tools.
    If agent_id is provided, checks the agent's tools first.
    Otherwise checks regular tools, then MCP servers.
    
    Args:
        agent_id: Optional agent ID to check for attached tools
        
    Returns:
        str: The tool ID for find_tools, or None if not found
    """
    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    if LETTA_API_KEY:
        headers["Authorization"] = f"Bearer {LETTA_API_KEY}"
    
    try:
        # If agent_id is provided, check agent's tools first
        if agent_id:
            agent_tools_url = f"{LETTA_URL}/agents/{agent_id}/tools"
            print(f"[TOOL_LOOKUP] Checking agent {agent_id} tools: {agent_tools_url}", file=sys.stderr)
            
            try:
                agent_response = requests.get(agent_tools_url, headers=headers, timeout=10)
                if agent_response.status_code == 200:
                    agent_tools = agent_response.json()
                    
                    # Look for find_tools in agent's tools
                    for tool in agent_tools:
                        tool_name = tool.get('name', '').lower()
                        tool_id = tool.get('id', '')
                        
                        if tool_name == 'find_tools':
                            print(f"[TOOL_LOOKUP] Found in agent's tools: {tool_id} (name: {tool_name})", file=sys.stderr)
                            return tool_id
                        
                        # Also check for variations
                        if 'find' in tool_name and 'tool' in tool_name:
                            print(f"[TOOL_LOOKUP] Found potential match in agent's tools: {tool_id} (name: {tool_name})", file=sys.stderr)
                            # Store as candidate but continue searching for exact match
                            candidate_id = tool_id
                    
                    # Return candidate if no exact match found
                    if 'candidate_id' in locals():
                        return candidate_id
                        
            except Exception as e:
                print(f"[TOOL_LOOKUP] Error checking agent tools: {e}", file=sys.stderr)
        
        # Fall back to checking all tools
        url = f"{LETTA_URL}/tools"
        print(f"[TOOL_LOOKUP] Querying all tools: {url}", file=sys.stderr)
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            tools = response.json()
            
            # Search for find_tools by name
            for tool in tools:
                tool_name = tool.get('name', '').lower()
                tool_id = tool.get('id', '')
                
                if tool_name == 'find_tools':
                    print(f"[TOOL_LOOKUP] Found in tools: {tool_id} (name: {tool_name})", file=sys.stderr)
                    return tool_id
        
        # Now try MCP servers
        mcp_url = f"{LETTA_URL}/tools/mcp/servers"
        print(f"[TOOL_LOOKUP] Querying MCP servers: {mcp_url}", file=sys.stderr)
        mcp_response = requests.get(mcp_url, headers=headers, timeout=10)
        
        if mcp_response.status_code == 200:
            mcp_servers = mcp_response.json()
            
            # Check each MCP server for find_tools
            for server_name, server_info in mcp_servers.items():
                print(f"[TOOL_LOOKUP] Checking MCP server: {server_name}", file=sys.stderr)
                
                # Get tools from this MCP server
                server_tools_url = f"{LETTA_URL}/tools/mcp/servers/{server_name}/tools"
                try:
                    tools_response = requests.get(server_tools_url, headers=headers, timeout=10)
                    if tools_response.status_code == 200:
                        server_tools = tools_response.json()
                        
                        for tool in server_tools:
                            tool_name = tool.get('name', '').lower()
                            
                            if tool_name == 'find_tools':
                                # MCP tools need to be looked up by their registered ID
                                print(f"[TOOL_LOOKUP] Found find_tools in MCP server: {server_name}", file=sys.stderr)
                                print(f"[TOOL_LOOKUP] Note: Need to find actual tool ID from agent or tools list", file=sys.stderr)
                                # Don't return a constructed ID, it won't work
                                
                except Exception as e:
                    print(f"[TOOL_LOOKUP] Error checking server {server_name}: {e}", file=sys.stderr)
        
        print("[TOOL_LOOKUP] Warning: Could not find find_tools tool in Letta API", file=sys.stderr)
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"[TOOL_LOOKUP] Error querying Letta API: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[TOOL_LOOKUP] Unexpected error: {e}", file=sys.stderr)
        return None

def get_find_tools_id_with_fallback(agent_id: Optional[str] = None, fallback_id: Optional[str] = None) -> str:
    """
    Get the find_tools ID with a fallback if dynamic lookup fails.
    
    Args:
        agent_id: Optional agent ID to check for attached tools
        fallback_id: The ID to use if dynamic lookup fails (if not provided, uses hardcoded fallback)
        
    Returns:
        str: The tool ID (either dynamically found or the fallback)
    """
    # Use the original hardcoded IDs as ultimate fallbacks
    if fallback_id is None:
        # These are the known tool IDs from the conversation history
        fallback_id = "tool-e34b5c60-5bd5-4288-a97f-2167ddf3062b"  # Original ID
        
    dynamic_id = get_find_tools_id(agent_id)
    if dynamic_id:
        return dynamic_id
    else:
        print(f"[TOOL_LOOKUP] Using fallback ID: {fallback_id}", file=sys.stderr)
        return fallback_id


def get_tool_id_by_name(tool_name: str) -> Optional[str]:
    """
    Find a tool ID by its name from the global tools list.
    
    Args:
        tool_name: The name of the tool to find
        
    Returns:
        str: The tool ID if found, None otherwise
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    if LETTA_API_KEY:
        headers["Authorization"] = f"Bearer {LETTA_API_KEY}"
    
    try:
        url = f"{LETTA_URL}/tools"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            tools = response.json()
            
            for tool in tools:
                if tool.get('name', '').lower() == tool_name.lower():
                    return tool.get('id')
        
        return None
        
    except Exception as e:
        print(f"[TOOL_LOOKUP] Error finding tool by name '{tool_name}': {e}", file=sys.stderr)
        return None


def get_agent_tool_names(agent_id: str) -> set:
    """
    Get the set of tool names currently attached to an agent.
    
    Args:
        agent_id: The agent ID
        
    Returns:
        set: Set of tool names (lowercase) attached to the agent
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    if LETTA_API_KEY:
        headers["Authorization"] = f"Bearer {LETTA_API_KEY}"
    
    try:
        url = f"{LETTA_URL}/agents/{agent_id}/tools"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            tools = response.json()
            return {tool.get('name', '').lower() for tool in tools if tool.get('name')}
        
        return set()
        
    except Exception as e:
        print(f"[TOOL_LOOKUP] Error getting agent tools: {e}", file=sys.stderr)
        return set()


def attach_tool_to_agent(agent_id: str, tool_id: str) -> bool:
    """
    Attach a tool to an agent via the Letta API.
    
    Args:
        agent_id: The agent ID
        tool_id: The tool ID to attach
        
    Returns:
        bool: True if successful, False otherwise
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    if LETTA_API_KEY:
        headers["Authorization"] = f"Bearer {LETTA_API_KEY}"
    
    try:
        url = f"{LETTA_URL}/agents/{agent_id}/tools/attach/{tool_id}"
        print(f"[PROTECTED_TOOLS] Attaching tool {tool_id} to agent {agent_id}", file=sys.stderr)
        
        response = requests.patch(url, headers=headers, json={}, timeout=10)
        
        if response.status_code in [200, 201]:
            print(f"[PROTECTED_TOOLS] Successfully attached tool {tool_id}", file=sys.stderr)
            return True
        elif response.status_code == 409:
            # Already attached
            print(f"[PROTECTED_TOOLS] Tool {tool_id} already attached (409)", file=sys.stderr)
            return True
        else:
            print(f"[PROTECTED_TOOLS] Failed to attach tool: {response.status_code} - {response.text}", file=sys.stderr)
            return False
            
    except Exception as e:
        print(f"[PROTECTED_TOOLS] Error attaching tool: {e}", file=sys.stderr)
        return False


def ensure_protected_tools(agent_id: str, protected_tools_config: str = None) -> dict:
    """
    Ensure protected tools are attached to an agent.
    
    This function checks if protected tools are attached to the agent,
    and attaches any missing ones. Protected tools are specified by name
    and looked up to get their IDs.
    
    Args:
        agent_id: The agent ID
        protected_tools_config: Comma-separated list of tool names to protect
                                (defaults to PROTECTED_TOOLS from config)
                                
    Returns:
        dict: Result with 'success' (bool), 'attached' (list), 'already_present' (list), 'failed' (list)
    """
    if not agent_id:
        return {"success": False, "error": "No agent_id provided", "attached": [], "already_present": [], "failed": []}
    
    # Get protected tools from config if not provided
    if protected_tools_config is None:
        from webhook_server.config import PROTECTED_TOOLS
        protected_tools_config = PROTECTED_TOOLS
    
    # Parse protected tool names
    protected_tool_names = [name.strip().lower() for name in protected_tools_config.split(',') if name.strip()]
    
    if not protected_tool_names:
        return {"success": True, "attached": [], "already_present": [], "failed": [], "message": "No protected tools configured"}
    
    print(f"[PROTECTED_TOOLS] Ensuring protected tools for agent {agent_id}: {protected_tool_names}", file=sys.stderr)
    
    # Get current agent tools
    current_tool_names = get_agent_tool_names(agent_id)
    print(f"[PROTECTED_TOOLS] Agent currently has tools: {current_tool_names}", file=sys.stderr)
    
    attached = []
    already_present = []
    failed = []
    
    for tool_name in protected_tool_names:
        if tool_name in current_tool_names:
            print(f"[PROTECTED_TOOLS] Tool '{tool_name}' already attached", file=sys.stderr)
            already_present.append(tool_name)
        else:
            # Need to attach this tool
            print(f"[PROTECTED_TOOLS] Tool '{tool_name}' missing, looking up ID...", file=sys.stderr)
            
            tool_id = get_tool_id_by_name(tool_name)
            
            if tool_id:
                if attach_tool_to_agent(agent_id, tool_id):
                    attached.append({"name": tool_name, "id": tool_id})
                else:
                    failed.append({"name": tool_name, "id": tool_id, "reason": "attach_failed"})
            else:
                print(f"[PROTECTED_TOOLS] Could not find tool ID for '{tool_name}'", file=sys.stderr)
                failed.append({"name": tool_name, "reason": "tool_not_found"})
    
    result = {
        "success": len(failed) == 0,
        "attached": attached,
        "already_present": already_present,
        "failed": failed
    }
    
    print(f"[PROTECTED_TOOLS] Result: {result}", file=sys.stderr)
    return result
