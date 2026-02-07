import requests
import json
from typing import Optional, Tuple

from .config import LETTA_API_HEADERS, get_api_url

def find_memory_block(agent_id: str, block_label: str) -> Tuple[Optional[dict], bool]:
    """
    Finds a memory block with a specific label for a given agent.
    
    Args:
        agent_id: The ID of the agent.
        block_label: The label of the block to find (e.g., 'graphiti_context').

    Returns:
        A tuple containing the block dictionary and a boolean indicating if the
        block is attached to the agent, or (None, False) if not found.
    """
    if not agent_id:
        print(f"[find_memory_block] No agent_id provided for label '{block_label}'.")
        return None, False

    try:
        # Stage 1: Check blocks attached to the agent
        agent_blocks_url = get_api_url(f"agents/{agent_id}/core-memory/blocks")
        request_headers = {**LETTA_API_HEADERS}
        
        agent_blocks_response = requests.get(agent_blocks_url, headers=request_headers, timeout=10)
        agent_blocks_response.raise_for_status()
        
        response_data = agent_blocks_response.json()
        
        # Handle case where response might be a list or a dict
        if isinstance(response_data, list):
            attached_blocks = response_data
        else:
            attached_blocks = response_data.get("blocks", [])
        for block in attached_blocks:
            if block.get("label") == block_label:
                print(f"[find_memory_block] Found attached '{block_label}' block (ID: {block.get('id')}).")
                return block, True

        # Stage 2: Check global blocks
        global_blocks_url = get_api_url("blocks")
        params = {"label": block_label, "templates_only": "false"}
        
        global_blocks_response = requests.get(global_blocks_url, headers=LETTA_API_HEADERS, params=params, timeout=10)
        global_blocks_response.raise_for_status()
        
        response_data = global_blocks_response.json()
        
        # Handle case where response might be a list or a dict
        if isinstance(response_data, list):
            global_blocks = response_data
        else:
            global_blocks = response_data.get("blocks", [])
        if global_blocks:
            block = global_blocks[0]
            print(f"[find_memory_block] Found global '{block_label}' block (ID: {block.get('id')}).")
            return block, False

        print(f"[find_memory_block] No '{block_label}' block found for agent {agent_id}.")
        return None, False

    except requests.exceptions.RequestException as e:
        print(f"[find_memory_block] API Error for agent {agent_id} and label '{block_label}': {e}")
        return None, False
    except Exception as e:
        print(f"[find_memory_block] Unexpected error for agent {agent_id} and label '{block_label}': {e}")
        return None, False