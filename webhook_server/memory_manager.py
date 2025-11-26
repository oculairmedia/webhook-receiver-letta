import requests
from typing import Dict, Any, Optional

from .config import LETTA_API_HEADERS, get_api_url
from .context_utils import _build_cumulative_context
from .block_finders import find_memory_block

def update_memory_block(block_id: str, block_data: Dict[str, Any], agent_id: Optional[str] = None, existing_block: Optional[dict] = None) -> Dict[str, Any]:
    """Update an existing memory block with new data using cumulative context."""
    new_context = block_data.get("value", "")
    existing_context = existing_block.get("value", "") if existing_block else ""
    
    cumulative_context = _build_cumulative_context(existing_context, new_context)
    
    update_data = {
        "value": cumulative_context,
        "metadata": block_data.get("metadata", {})
    }
    
    headers = LETTA_API_HEADERS.copy()
    if agent_id:
        headers["user_id"] = agent_id
        
    update_url = get_api_url(f"blocks/{block_id}")
    update_response = requests.patch(update_url, json=update_data, headers=headers)
    update_response.raise_for_status()
    
    return update_response.json()

def attach_block_to_agent(agent_id: str, block_id: str) -> bool:
    """Attach a block to an agent's core memory."""
    try:
        # Defensive fix: Handle case where block_id might be passed as a list
        if isinstance(block_id, list):
            if len(block_id) > 0:
                block_id = block_id[0]  # Take the first element
                print(f"[attach_block_to_agent] Warning: block_id was passed as list, using first element: {block_id}")
            else:
                print(f"[attach_block_to_agent] Error: block_id was passed as empty list")
                return False
        
        # Ensure block_id is a string
        block_id = str(block_id)
        
        attach_url = get_api_url(f"agents/{agent_id}/core-memory/blocks/attach/{block_id}")
        headers = LETTA_API_HEADERS.copy()
        headers["user_id"] = agent_id
        
        # Send empty JSON body to avoid proxy error
        attach_response = requests.patch(attach_url, headers=headers, json={})
        
        # Handle 409 Conflict (block already attached) as success
        if attach_response.status_code == 409:
            print(f"[attach_block_to_agent] Block {block_id} already attached to agent {agent_id}")
            return True
        
        attach_response.raise_for_status()
        
        print(f"[attach_block_to_agent] Successfully attached block {block_id} to agent {agent_id}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"[attach_block_to_agent] Failed to attach block {block_id} to agent {agent_id}: {e}")
        return False

def create_memory_block(block_data: Dict[str, Any], agent_id: Optional[str] = None) -> Dict[str, Any]:
    """Create or update a memory block in Letta with auto-attachment."""
    block_label = block_data.get("label", "graphiti_context")
    
    if agent_id:
        block_to_use, is_attached = find_memory_block(agent_id, block_label)
        if block_to_use:
            # If block exists but not attached, attach it
            if not is_attached:
                print(f"[create_memory_block] Block exists but not attached. Auto-attaching...")
                attach_block_to_agent(agent_id, block_to_use['id'])
            
            # Update the existing block
            return update_memory_block(block_to_use['id'], block_data, agent_id, block_to_use)

    # If no block is found or no agent_id, create a new one
    create_url = get_api_url("blocks")
    headers = LETTA_API_HEADERS.copy()
    if agent_id:
        headers["user_id"] = agent_id

    create_response = requests.post(create_url, json=block_data, headers=headers)
    create_response.raise_for_status()
    
    new_block = create_response.json()
    
    # Auto-attach the newly created block to the agent
    if agent_id and new_block.get('id'):
        print(f"[create_memory_block] Auto-attaching newly created block {new_block['id']} to agent {agent_id}")
        attach_block_to_agent(agent_id, new_block['id'])
    
    return new_block

def create_tool_inventory_block(agent_id: str, content: str) -> Dict[str, Any]:
    """
    Create or replace the tool inventory block for an agent.
    Unlike cumulative context blocks, this is a fresh snapshot each time.
    
    Args:
        agent_id: The agent ID
        content: The formatted tool inventory content
        
    Returns:
        The created/updated block dict
    """
    if not agent_id or not content:
        print(f"[create_tool_inventory_block] Missing agent_id or content")
        return {}
    
    block_label = "available_tools"
    
    # Check if block already exists
    block_to_use, is_attached = find_memory_block(agent_id, block_label)
    
    block_data = {
        "label": block_label,
        "value": content,  # Fresh snapshot, no cumulative context
        "metadata": {"source": "tool_inventory", "type": "snapshot"}
    }
    
    if block_to_use:
        # Update existing block (replace content entirely)
        print(f"[create_tool_inventory_block] Updating existing {block_label} block")
        
        # If not attached, attach it first
        if not is_attached:
            print(f"[create_tool_inventory_block] Block exists but not attached. Auto-attaching...")
            attach_block_to_agent(agent_id, block_to_use['id'])
        
        # Update the block with fresh content (no cumulative logic)
        update_data = {
            "value": content,
            "metadata": block_data["metadata"]
        }
        
        headers = LETTA_API_HEADERS.copy()
        headers["user_id"] = agent_id
        
        update_url = get_api_url(f"blocks/{block_to_use['id']}")
        update_response = requests.patch(update_url, json=update_data, headers=headers)
        update_response.raise_for_status()
        
        return update_response.json()
    else:
        # Create new block
        print(f"[create_tool_inventory_block] Creating new {block_label} block")
        
        create_url = get_api_url("blocks")
        headers = LETTA_API_HEADERS.copy()
        headers["user_id"] = agent_id
        
        create_response = requests.post(create_url, json=block_data, headers=headers)
        create_response.raise_for_status()
        
        new_block = create_response.json()
        
        # Auto-attach to agent
        if new_block.get('id'):
            print(f"[create_tool_inventory_block] Auto-attaching new block {new_block['id']}")
            attach_block_to_agent(agent_id, new_block['id'])
        
        return new_block