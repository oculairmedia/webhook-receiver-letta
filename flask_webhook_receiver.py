
#!/usr/bin/env python3
"""
Flask-based server to receive webhooks from Letta, retrieve context from Graphiti,
and return it. This is an alternative to the FastAPI version that avoids Pydantic
dependency issues.
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime, UTC
import requests

from flask import Flask, request, jsonify
import threading

# Import arXiv integration
try:
    from arxiv_integration import ArxivIntegration
    arxiv_integration = ArxivIntegration()
    ARXIV_AVAILABLE = True
    print("[INIT] arXiv integration loaded successfully")
except ImportError as e:
    ARXIV_AVAILABLE = False
    print(f"[INIT] arXiv integration not available: {e}")
    arxiv_integration = None

# Default configuration
LETTA_BASE_URL = os.environ.get("LETTA_BASE_URL", "https://letta2.oculair.ca")
LETTA_PASSWORD = os.environ.get("LETTA_PASSWORD", "lettaSecurePass123")
LETTA_API_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-BARE-PASSWORD": f"password {LETTA_PASSWORD}",
    "Authorization": f"Bearer {LETTA_PASSWORD}"
}

# Maximum context snippet length for cumulative context
MAX_CONTEXT_SNIPPET_LENGTH = 6000

# Agent tracking for Matrix notifications
MATRIX_CLIENT_URL = os.environ.get("MATRIX_CLIENT_URL", "http://192.168.50.90:8004")
known_agents = set()
agent_tracking_lock = threading.Lock()

def get_api_url(path: str) -> str:
    """Construct API URL following Letta's v1 convention."""
    base = f"{LETTA_BASE_URL}/v1".rstrip("/")
    path = path.lstrip("/")
    return f"{base}/{path}"

def track_agent_and_notify(agent_id: str) -> None:
    """Track agent and notify Matrix client if new agent is detected."""
    if not agent_id or not agent_id.startswith("agent-"):
        return
    
    with agent_tracking_lock:
        if agent_id not in known_agents:
            print(f"[AGENT_TRACKER] New agent detected: {agent_id}")
            known_agents.add(agent_id)
            
            # Notify Matrix client in background thread
            def notify_matrix():
                try:
                    notify_url = f"{MATRIX_CLIENT_URL}/webhook/new-agent"
                    payload = {"agent_id": agent_id, "timestamp": datetime.now(UTC).isoformat()}
                    response = requests.post(notify_url, json=payload, timeout=5)
                    if response.status_code == 200:
                        print(f"[AGENT_TRACKER] Successfully notified Matrix client about new agent: {agent_id}")
                    else:
                        print(f"[AGENT_TRACKER] Failed to notify Matrix client: {response.status_code} - {response.text}")
                except Exception as e:
                    print(f"[AGENT_TRACKER] Error notifying Matrix client: {e}")
            
            # Run notification in background to avoid blocking webhook processing
            threading.Thread(target=notify_matrix, daemon=True).start()
        else:
            print(f"[AGENT_TRACKER] Known agent: {agent_id}")

def find_context_block(agent_id: str) -> tuple[Optional[dict], bool]:
    """
    Finds a 'graphiti_context' block for a given agent.
    First checks blocks attached to the agent, then checks global blocks.
    Returns: (block_dict, is_attached_to_this_agent) or (None, False)
    """
    if not agent_id:
        print("[find_context_block] No agent_id provided.")
        return None, False
        
    try:
        # Stage 1: Check blocks already attached to this agent
        agent_blocks_url = get_api_url(f"agents/{agent_id}/core-memory/blocks")
        print(f"[find_context_block] Stage 1: Checking blocks attached to agent {agent_id} via URL: {agent_blocks_url}")
        
        request_headers = {**LETTA_API_HEADERS, "user_id": agent_id}
        agent_blocks_response = requests.get(agent_blocks_url, headers=request_headers, timeout=10)
        
        print(f"[find_context_block] Attached blocks - Status: {agent_blocks_response.status_code}")
        if agent_blocks_response.status_code != 200:
            print(f"[find_context_block] Attached blocks - Response Text: {agent_blocks_response.text}")
        agent_blocks_response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        
        attached_response_data = agent_blocks_response.json()
        print(f"[find_context_block] Attached blocks - Full JSON: {json.dumps(attached_response_data, indent=2)}")

        attached_blocks_list = []
        if isinstance(attached_response_data, list):
            attached_blocks_list = attached_response_data
        elif isinstance(attached_response_data, dict):
            attached_blocks_list = attached_response_data.get("blocks", []) # Common pattern for wrapped lists
        
        print(f"[find_context_block] Processing {len(attached_blocks_list)} blocks reported as attached to agent {agent_id}.")
        for block in attached_blocks_list:
            block_id = block.get("id", "N/A")
            block_label = block.get("label")
            block_name = block.get("name", "N/A")
            print(f"[find_context_block]   Checking attached block: ID='{block_id}', Label='{block_label}', Name='{block_name}'")
            if block_label == "graphiti_context":
                print(f"[find_context_block] SUCCESS: Found 'graphiti_context' block (ID: {block_id}) already attached.")
                return block, True # Block found and is confirmed attached

        # Stage 2: If not found attached, check global blocks for a usable unattached one
        print(f"[find_context_block] Stage 2: No 'graphiti_context' block found attached to agent {agent_id}. Checking global blocks...")
        global_blocks_url = get_api_url("blocks")
        params = {"label": "graphiti_context", "templates_only": "false"} # Filter by label at API level
        
        print(f"[find_context_block] Querying global blocks: URL='{global_blocks_url}', Params='{params}'")
        global_blocks_response = requests.get(global_blocks_url, headers=LETTA_API_HEADERS, params=params, timeout=10)
        
        print(f"[find_context_block] Global blocks - Status: {global_blocks_response.status_code}")
        if global_blocks_response.status_code != 200:
            print(f"[find_context_block] Global blocks - Response Text: {global_blocks_response.text}")
        global_blocks_response.raise_for_status()

        global_response_data = global_blocks_response.json()
        print(f"[find_context_block] Global blocks - Full JSON: {json.dumps(global_response_data, indent=2)}")

        global_blocks_list = []
        if isinstance(global_response_data, list):
            global_blocks_list = global_response_data
        elif isinstance(global_response_data, dict):
            global_blocks_list = global_response_data.get("blocks", [])

        print(f"[find_context_block] Found {len(global_blocks_list)} global blocks matching label 'graphiti_context'.")
        if global_blocks_list:
            # Prefer the first one found. Could add more complex selection logic if needed.
            unattached_block_to_use = global_blocks_list[0]
            block_id = unattached_block_to_use.get("id", "N/A")
            print(f"[find_context_block] SUCCESS: Found unattached global 'graphiti_context' block (ID: {block_id}) to use.")
            return unattached_block_to_use, False # Block found, but is not (yet) attached to this agent

        print("[find_context_block] No 'graphiti_context' block found (neither attached nor globally available).")
        return None, False

    except requests.exceptions.Timeout:
        print(f"[find_context_block] Timeout while trying to list blocks for agent {agent_id}.")
        return None, False
    except requests.exceptions.RequestException as e:
        print(f"[find_context_block] API Error for agent {agent_id}: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"[find_context_block] Error response content: {e.response.text}")
        return None, False
    except Exception as e:
        print(f"[find_context_block] Unexpected error: {str(e)}")
        return None, False

def find_bigquery_block(agent_id: str) -> tuple[Optional[dict], bool]:
    """
    Finds a 'bigquery' block for a given agent.
    First checks blocks attached to the agent, then checks global blocks.
    Returns: (block_dict, is_attached_to_this_agent) or (None, False)
    """
    if not agent_id:
        print("[find_bigquery_block] No agent_id provided.")
        return None, False
        
    try:
        # Stage 1: Check blocks already attached to this agent
        agent_blocks_url = get_api_url(f"agents/{agent_id}/core-memory/blocks")
        print(f"[find_bigquery_block] Stage 1: Checking blocks attached to agent {agent_id} via URL: {agent_blocks_url}")
        
        request_headers = {**LETTA_API_HEADERS, "user_id": agent_id}
        agent_blocks_response = requests.get(agent_blocks_url, headers=request_headers, timeout=10)
        
        print(f"[find_bigquery_block] Attached blocks - Status: {agent_blocks_response.status_code}")
        if agent_blocks_response.status_code != 200:
            print(f"[find_bigquery_block] Attached blocks - Response Text: {agent_blocks_response.text}")
        agent_blocks_response.raise_for_status()
        
        attached_response_data = agent_blocks_response.json()
        print(f"[find_bigquery_block] Attached blocks - Full JSON: {json.dumps(attached_response_data, indent=2)}")

        attached_blocks_list = []
        if isinstance(attached_response_data, list):
            attached_blocks_list = attached_response_data
        elif isinstance(attached_response_data, dict):
            attached_blocks_list = attached_response_data.get("blocks", [])
        
        print(f"[find_bigquery_block] Processing {len(attached_blocks_list)} blocks reported as attached to agent {agent_id}.")
        for block in attached_blocks_list:
            block_id = block.get("id", "N/A")
            block_label = block.get("label")
            block_name = block.get("name", "N/A")
            print(f"[find_bigquery_block]   Checking attached block: ID='{block_id}', Label='{block_label}', Name='{block_name}'")
            if block_label == "bigquery":
                print(f"[find_bigquery_block] SUCCESS: Found 'bigquery' block (ID: {block_id}) already attached.")
                return block, True

        # Stage 2: If not found attached, check global blocks for a usable unattached one
        print(f"[find_bigquery_block] Stage 2: No 'bigquery' block found attached to agent {agent_id}. Checking global blocks...")
        global_blocks_url = get_api_url("blocks")
        params = {"label": "bigquery", "templates_only": "false"}
        
        print(f"[find_bigquery_block] Querying global blocks: URL='{global_blocks_url}', Params='{params}'")
        global_blocks_response = requests.get(global_blocks_url, headers=LETTA_API_HEADERS, params=params, timeout=10)
        
        print(f"[find_bigquery_block] Global blocks - Status: {global_blocks_response.status_code}")
        if global_blocks_response.status_code != 200:
            print(f"[find_bigquery_block] Global blocks - Response Text: {global_blocks_response.text}")
        global_blocks_response.raise_for_status()

        global_response_data = global_blocks_response.json()
        print(f"[find_bigquery_block] Global blocks - Full JSON: {json.dumps(global_response_data, indent=2)}")

        global_blocks_list = []
        if isinstance(global_response_data, list):
            global_blocks_list = global_response_data
        elif isinstance(global_response_data, dict):
            global_blocks_list = global_response_data.get("blocks", [])

        print(f"[find_bigquery_block] Found {len(global_blocks_list)} global blocks matching label 'bigquery'.")
        if global_blocks_list:
            unattached_block_to_use = global_blocks_list[0]
            block_id = unattached_block_to_use.get("id", "N/A")
            print(f"[find_bigquery_block] SUCCESS: Found unattached global 'bigquery' block (ID: {block_id}) to use.")
            return unattached_block_to_use, False

        print("[find_bigquery_block] No 'bigquery' block found (neither attached nor globally available).")
        return None, False

    except requests.exceptions.Timeout:
        print(f"[find_bigquery_block] Timeout while trying to list blocks for agent {agent_id}.")
        return None, False
    except requests.exceptions.RequestException as e:
        print(f"[find_bigquery_block] API Error for agent {agent_id}: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"[find_bigquery_block] Error response content: {e.response.text}")
        return None, False
    except Exception as e:
        print(f"[find_bigquery_block] Unexpected error: {str(e)}")
        return None, False

def find_arxiv_block(agent_id: str) -> tuple[Optional[dict], bool]:
    """
    Finds a 'arxiv_papers' block for a given agent.
    First checks blocks attached to the agent, then checks global blocks.
    Returns: (block_dict, is_attached_to_this_agent) or (None, False)
    """
    if not agent_id:
        print("[find_arxiv_block] No agent_id provided.")
        return None, False
        
    try:
        # Stage 1: Check blocks already attached to this agent
        agent_blocks_url = get_api_url(f"agents/{agent_id}/core-memory/blocks")
        print(f"[find_arxiv_block] Stage 1: Checking blocks attached to agent {agent_id} via URL: {agent_blocks_url}")
        
        request_headers = {**LETTA_API_HEADERS, "user_id": agent_id}
        agent_blocks_response = requests.get(agent_blocks_url, headers=request_headers, timeout=10)
        
        print(f"[find_arxiv_block] Attached blocks - Status: {agent_blocks_response.status_code}")
        if agent_blocks_response.status_code != 200:
            print(f"[find_arxiv_block] Attached blocks - Response Text: {agent_blocks_response.text}")
        agent_blocks_response.raise_for_status()
        
        attached_response_data = agent_blocks_response.json()
        print(f"[find_arxiv_block] Attached blocks - Full JSON: {json.dumps(attached_response_data, indent=2)}")

        attached_blocks_list = []
        if isinstance(attached_response_data, list):
            attached_blocks_list = attached_response_data
        elif isinstance(attached_response_data, dict):
            attached_blocks_list = attached_response_data.get("blocks", [])
        
        print(f"[find_arxiv_block] Processing {len(attached_blocks_list)} blocks reported as attached to agent {agent_id}.")
        for block in attached_blocks_list:
            block_id = block.get("id", "N/A")
            block_label = block.get("label")
            block_name = block.get("name", "N/A")
            print(f"[find_arxiv_block]   Checking attached block: ID='{block_id}', Label='{block_label}', Name='{block_name}'")
            if block_label == "arxiv_papers":
                print(f"[find_arxiv_block] SUCCESS: Found 'arxiv_papers' block (ID: {block_id}) already attached.")
                return block, True

        # Stage 2: If not found attached, check global blocks for a usable unattached one
        print(f"[find_arxiv_block] Stage 2: No 'arxiv_papers' block found attached to agent {agent_id}. Checking global blocks...")
        global_blocks_url = get_api_url("blocks")
        params = {"label": "arxiv_papers", "templates_only": "false"}
        
        print(f"[find_arxiv_block] Querying global blocks: URL='{global_blocks_url}', Params='{params}'")
        global_blocks_response = requests.get(global_blocks_url, headers=LETTA_API_HEADERS, params=params, timeout=10)
        
        print(f"[find_arxiv_block] Global blocks - Status: {global_blocks_response.status_code}")
        if global_blocks_response.status_code != 200:
            print(f"[find_arxiv_block] Global blocks - Response Text: {global_blocks_response.text}")
        global_blocks_response.raise_for_status()

        global_response_data = global_blocks_response.json()
        print(f"[find_arxiv_block] Global blocks - Full JSON: {json.dumps(global_response_data, indent=2)}")

        global_blocks_list = []
        if isinstance(global_response_data, list):
            global_blocks_list = global_response_data
        elif isinstance(global_response_data, dict):
            global_blocks_list = global_response_data.get("blocks", [])

        print(f"[find_arxiv_block] Found {len(global_blocks_list)} global blocks matching label 'arxiv_papers'.")
        if global_blocks_list:
            unattached_block_to_use = global_blocks_list[0]
            block_id = unattached_block_to_use.get("id", "N/A")
            print(f"[find_arxiv_block] SUCCESS: Found unattached global 'arxiv_papers' block (ID: {block_id}) to use.")
            return unattached_block_to_use, False

        print("[find_arxiv_block] No 'arxiv_papers' block found (neither attached nor globally available).")
        return None, False

    except requests.exceptions.Timeout:
        print(f"[find_arxiv_block] Timeout while trying to list blocks for agent {agent_id}.")
        return None, False
    except requests.exceptions.RequestException as e:
        print(f"[find_arxiv_block] API Error for agent {agent_id}: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"[find_arxiv_block] Error response content: {e.response.text}")
        return None, False
    except Exception as e:
        print(f"[find_arxiv_block] Unexpected error: {str(e)}")
        return None, False

def find_gdelt_block(agent_id: str) -> tuple[Optional[dict], bool]:
    """
    Finds a 'gdelt_news' block for a given agent.
    First checks blocks attached to the agent, then checks global blocks.
    Returns: (block_dict, is_attached_to_this_agent) or (None, False)
    """
    if not agent_id:
        print("[find_gdelt_block] No agent_id provided.")
        return None, False
        
    try:
        # Stage 1: Check blocks already attached to this agent
        agent_blocks_url = get_api_url(f"agents/{agent_id}/core-memory/blocks")
        print(f"[find_gdelt_block] Stage 1: Checking blocks attached to agent {agent_id} via URL: {agent_blocks_url}")
        
        request_headers = {**LETTA_API_HEADERS, "user_id": agent_id}
        agent_blocks_response = requests.get(agent_blocks_url, headers=request_headers, timeout=10)
        
        print(f"[find_gdelt_block] Attached blocks - Status: {agent_blocks_response.status_code}")
        if agent_blocks_response.status_code != 200:
            print(f"[find_gdelt_block] Attached blocks - Response Text: {agent_blocks_response.text}")
        agent_blocks_response.raise_for_status()
        
        attached_response_data = agent_blocks_response.json()
        print(f"[find_gdelt_block] Attached blocks - Full JSON: {json.dumps(attached_response_data, indent=2)}")

        attached_blocks_list = []
        if isinstance(attached_response_data, list):
            attached_blocks_list = attached_response_data
        elif isinstance(attached_response_data, dict):
            attached_blocks_list = attached_response_data.get("blocks", [])
        
        print(f"[find_gdelt_block] Processing {len(attached_blocks_list)} blocks reported as attached to agent {agent_id}.")
        for block in attached_blocks_list:
            block_id = block.get("id", "N/A")
            block_label = block.get("label")
            block_name = block.get("name", "N/A")
            print(f"[find_gdelt_block]   Checking attached block: ID='{block_id}', Label='{block_label}', Name='{block_name}'")
            if block_label == "gdelt_news":
                print(f"[find_gdelt_block] SUCCESS: Found 'gdelt_news' block (ID: {block_id}) already attached.")
                return block, True

        # Stage 2: If not found attached, check global blocks for a usable unattached one
        print(f"[find_gdelt_block] Stage 2: No 'gdelt_news' block found attached to agent {agent_id}. Checking global blocks...")
        global_blocks_url = get_api_url("blocks")
        params = {"label": "gdelt_news", "templates_only": "false"}
        
        print(f"[find_gdelt_block] Querying global blocks: URL='{global_blocks_url}', Params='{params}'")
        global_blocks_response = requests.get(global_blocks_url, headers=LETTA_API_HEADERS, params=params, timeout=10)
        
        print(f"[find_gdelt_block] Global blocks - Status: {global_blocks_response.status_code}")
        if global_blocks_response.status_code != 200:
            print(f"[find_gdelt_block] Global blocks - Response Text: {global_blocks_response.text}")
        global_blocks_response.raise_for_status()

        global_response_data = global_blocks_response.json()
        print(f"[find_gdelt_block] Global blocks - Full JSON: {json.dumps(global_response_data, indent=2)}")

        global_blocks_list = []
        if isinstance(global_response_data, list):
            global_blocks_list = global_response_data
        elif isinstance(global_response_data, dict):
            global_blocks_list = global_response_data.get("blocks", [])

        print(f"[find_gdelt_block] Found {len(global_blocks_list)} global blocks matching label 'gdelt_news'.")
        if global_blocks_list:
            unattached_block_to_use = global_blocks_list[0]
            block_id = unattached_block_to_use.get("id", "N/A")
            print(f"[find_gdelt_block] SUCCESS: Found unattached global 'gdelt_news' block (ID: {block_id}) to use.")
            return unattached_block_to_use, False

        print("[find_gdelt_block] No 'gdelt_news' block found (neither attached nor globally available).")
        return None, False

    except requests.exceptions.Timeout:
        print(f"[find_gdelt_block] Timeout while trying to list blocks for agent {agent_id}.")
        return None, False
    except requests.exceptions.RequestException as e:
        print(f"[find_gdelt_block] API Error for agent {agent_id}: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"[find_gdelt_block] Error response content: {e.response.text}")
        return None, False
    except Exception as e:
        print(f"[find_gdelt_block] Unexpected error: {str(e)}")
        return None, False

def update_memory_block(block_id: str, block_data: Dict[str, Any], agent_id: Optional[str] = None, existing_block: Optional[dict] = None) -> Dict[str, Any]:
    """Update an existing memory block with new data using cumulative context."""
    try:
        # Get the new context from block_data
        new_context = block_data.get("value", "")
        
        # Get existing context from the existing_block or fetch it
        existing_context = ""
        if existing_block:
            existing_context = existing_block.get("value", "")
        else:
            # Fetch the current block to get existing context
            try:
                headers = LETTA_API_HEADERS.copy()
                if agent_id:
                    headers["user_id"] = agent_id
                
                get_url = get_api_url(f"blocks/{block_id}")
                get_response = requests.get(get_url, headers=headers)
                get_response.raise_for_status()
                current_block = get_response.json()
                existing_context = current_block.get("value", "")
            except requests.exceptions.RequestException as e:
                print(f"[update_memory_block] Warning: Could not fetch existing block context: {e}")
                existing_context = ""
        
        # Build cumulative context
        cumulative_context = _build_cumulative_context(existing_context, new_context)
        
        # Prepare update data according to Letta's API format
        update_data = {
            "value": cumulative_context,
            "metadata": block_data.get("metadata", {})
        }
        
        # Add headers for agent if provided
        headers = LETTA_API_HEADERS.copy()
        if agent_id:
            headers["user_id"] = agent_id
            
        # Update using PATCH request
        update_url = get_api_url(f"blocks/{block_id}")
        update_response = requests.patch(
            update_url,
            json=update_data,
            headers=headers
        )
        update_response.raise_for_status()
        
        response_data = update_response.json()
        return {
            "success": True,
            "block_id": block_id,
            "block": response_data,
            "message": "Memory block updated successfully with cumulative context",
            "updated": True
        }
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to update memory block: {str(e)}")

def create_memory_block(block_data: Dict[str, Any], agent_id: Optional[str] = None) -> Dict[str, Any]:
    """Create or update a memory block in Letta."""
    try:
        result = {}
        block_to_use_info, is_already_attached = (None, False)
        block_label = block_data.get("label", "graphiti_context")

        if agent_id:
            print(f"[create_memory_block] Agent ID '{agent_id}' provided. Looking for existing block with label '{block_label}'.")
            
            # Use the appropriate find function based on the label
            if block_label == "graphiti_context":
                block_to_use_info, is_already_attached = find_context_block(agent_id)
            elif block_label == "arxiv_papers":
                block_to_use_info, is_already_attached = find_arxiv_block(agent_id)
            elif block_label == "bigquery":
                block_to_use_info, is_already_attached = find_bigquery_block(agent_id)
            elif block_label == "gdelt_news":
                block_to_use_info, is_already_attached = find_gdelt_block(agent_id)
            else:
                # For other labels, don't reuse existing blocks
                print(f"[create_memory_block] Label '{block_label}' doesn't have a specific find function. Will create new block.")
        else:
            print("[create_memory_block] No Agent ID provided. Will create a global block.")

        if block_to_use_info:
            block_id_to_use = block_to_use_info.get("id")
            if not block_id_to_use:
                print("[create_memory_block] Warning: find_context_block returned a block without an ID. Forcing new block creation.")
                block_to_use_info = None # This will trigger the 'create new' path below
            else:
                status_description = "already attached" if is_already_attached else "found globally (will be attached/ensured)"
                print(f"[create_memory_block] Using existing block (ID: {block_id_to_use}, Status: {status_description}). Updating its content.")
                
                result = update_memory_block(
                    block_id=block_id_to_use,
                    block_data=block_data, # block_data is the new content
                    agent_id=agent_id,     # Pass agent_id for user_id header in PATCH
                    existing_block=block_to_use_info  # Pass the existing block for cumulative context
                )
                # Preserve original name if updating an existing block, otherwise use new generated name
                result["block_name"] = block_to_use_info.get("name", block_data.get("name"))
                
                # If the block was found globally (is_already_attached is False) or even if it was attached,
                # ensuring attachment is idempotent and good practice.
                if agent_id: # This check is vital; only attach if there's an agent.
                    print(f"[create_memory_block] Ensuring block {block_id_to_use} is attached to agent {agent_id}.")
                    attach_url = get_api_url(f"agents/{agent_id}/core-memory/blocks/attach/{block_id_to_use}")
                    attach_headers = {**LETTA_API_HEADERS, "user_id": agent_id}
                    attach_response = requests.patch(attach_url, headers=attach_headers, json={})
                    attach_response.raise_for_status()
                    print(f"[create_memory_block] Block {block_id_to_use} attachment to agent {agent_id} confirmed/ensured.")
        
        # This 'if' condition will be met if:
        # 1. No agent_id was initially provided.
        # 2. agent_id was provided, but find function returned (None, False).
        # 3. agent_id was provided, find function returned a block, but that block had no ID (forced to None).
        if not block_to_use_info:
            log_message = f"No existing '{block_label}' block found for agent {agent_id}." if agent_id else "No agent_id provided."
            print(f"[create_memory_block] {log_message} Creating a new block.")

            blocks_url = get_api_url("blocks") # Global block creation endpoint
            create_response = requests.post(blocks_url, json=block_data, headers=LETTA_API_HEADERS)
            create_response.raise_for_status()
            created_block_json = create_response.json()
            
            new_block_id = created_block_json.get("id") if isinstance(created_block_json, dict) else None
            if isinstance(created_block_json, list) and created_block_json: # Should not happen for POST /blocks
                 new_block_id = created_block_json[0].get("id")

            if not new_block_id:
                raise ValueError("[create_memory_block] Critical: No block ID returned from create endpoint after creating new block.")
            
            new_block_name = block_data.get("name") # Name from the input data used for creation

            result = {
                "success": True, "block_id": new_block_id, "block_name": new_block_name,
                "message": f"Memory block {new_block_name} created successfully", "updated": False
            }
            
            if agent_id: # If an agent_id was involved in this flow, attach the new block
                print(f"[create_memory_block] Attaching newly created block {new_block_id} to agent {agent_id}.")
                attach_url = get_api_url(f"agents/{agent_id}/core-memory/blocks/attach/{new_block_id}")
                attach_headers = {**LETTA_API_HEADERS, "user_id": agent_id}
                attach_response = requests.patch(attach_url, headers=attach_headers, json={})
                attach_response.raise_for_status()
                print(f"[create_memory_block] New block {new_block_id} attached successfully to agent {agent_id}.")
        
        # Final step: Add/Update agent info to the result if agent_id is present and operation was successful
        if agent_id and result.get("success"):
            # Get basic agent info
            agent_info_response = requests.get(
                get_api_url(f"agents/{agent_id}"),
                headers=LETTA_API_HEADERS
            )
            agent_info_response.raise_for_status()
            agent_info_data = agent_info_response.json()
            
            agent_name_from_api = "Unknown"
            if isinstance(agent_info_data, list) and agent_info_data:
                agent_name_from_api = agent_info_data[0].get("name", "Unknown")
            elif isinstance(agent_info_data, dict):
                agent_name_from_api = agent_info_data.get("name", "Unknown")
            
            # Get identity information attached to the agent
            try:
                # First, get the identity IDs from the agent information
                identity_ids = agent_info_data.get("identity_ids", [])
                
                if not identity_ids:
                    print(f"[create_memory_block] No identity IDs found for agent {agent_id}")
                    # Still update with basic agent info even if no identity IDs found
                    result.update({
                        "agent_id": agent_id,
                        "agent_name": agent_name_from_api
                    })
                else:
                    print(f"[create_memory_block] Found {len(identity_ids)} identity IDs for agent {agent_id}: {', '.join(identity_ids)}")
                    
                    # Initialize result update with agent info
                    result_update = {
                        "agent_id": agent_id,
                        "agent_name": agent_name_from_api
                    }
                    
                    # Retrieve identity information for each identity ID
                    identities = []
                    for identity_id in identity_ids:
                        identity_response = requests.get(
                            get_api_url(f"identities/{identity_id}"),
                            headers=LETTA_API_HEADERS,
                            timeout=10
                        )
                        
                        if identity_response.status_code != 200:
                            print(f"[create_memory_block] Error retrieving identity {identity_id}: {identity_response.status_code}")
                            continue
                        
                        identity_data = identity_response.json()
                        identities.append(identity_data)
                        
                        # If this is the first identity, use it as the primary identity for backward compatibility
                        if len(identities) == 1:
                            user_identity = identity_data
                            print(f"[create_memory_block] Found identity for agent {agent_id}: {json.dumps(user_identity, indent=2)}")
                            
                            # Add identity information to result
                            identity_id = user_identity.get("id")
                            if identity_id:
                                result_update["identity_id"] = identity_id
                            
                            # Add other relevant identity fields
                            for field in ["name", "identifier_key"]:
                                if field in user_identity and user_identity[field]:
                                    result_update[f"identity_{field}"] = user_identity[field]
                            
                            # Map identity_type to a role field for compatibility
                            identity_type = user_identity.get("identity_type")
                            if identity_type:
                                result_update["identity_role"] = identity_type
                    
                    # Add all identities to the result for completeness
                    if identities:
                        result_update["identities"] = identities
                    
                    result.update(result_update)
            except requests.exceptions.RequestException as e:
                print(f"[create_memory_block] Error retrieving identity for agent {agent_id}: {str(e)}")
                # Still update with basic agent info even if identity retrieval fails
                result.update({
                    "agent_id": agent_id,
                    "agent_name": agent_name_from_api
                })
            
        return result
        
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to interact with Letta API: {str(e)}")

def create_bigquery_memory_block(block_data: Dict[str, Any], agent_id: Optional[str] = None) -> Dict[str, Any]:
    """Create or update a BigQuery memory block in Letta."""
    try:
        result = {}
        block_to_use_info, is_already_attached = (None, False)

        if agent_id:
            print(f"[create_bigquery_memory_block] Agent ID '{agent_id}' provided. Looking for existing BigQuery block.")
            block_to_use_info, is_already_attached = find_bigquery_block(agent_id)
        else:
            print("[create_bigquery_memory_block] No Agent ID provided. Will create a global BigQuery block.")

        if block_to_use_info:
            block_id_to_use = block_to_use_info.get("id")
            if not block_id_to_use:
                print("[create_bigquery_memory_block] Warning: find_bigquery_block returned a block without an ID. Forcing new block creation.")
                block_to_use_info = None
            else:
                status_description = "already attached" if is_already_attached else "found globally (will be attached/ensured)"
                print(f"[create_bigquery_memory_block] Using existing BigQuery block (ID: {block_id_to_use}, Status: {status_description}). Updating its content.")
                
                result = update_memory_block(
                    block_id=block_id_to_use,
                    block_data=block_data,
                    agent_id=agent_id,
                    existing_block=block_to_use_info
                )
                result["block_name"] = block_to_use_info.get("name", block_data.get("name"))
                
                if agent_id:
                    print(f"[create_bigquery_memory_block] Ensuring BigQuery block {block_id_to_use} is attached to agent {agent_id}.")
                    attach_url = get_api_url(f"agents/{agent_id}/core-memory/blocks/attach/{block_id_to_use}")
                    attach_headers = {**LETTA_API_HEADERS, "user_id": agent_id}
                    attach_response = requests.patch(attach_url, headers=attach_headers, json={})
                    attach_response.raise_for_status()
                    print(f"[create_bigquery_memory_block] BigQuery block {block_id_to_use} attachment to agent {agent_id} confirmed/ensured.")
        
        if not block_to_use_info:
            log_message = f"No existing 'bigquery' block found for agent {agent_id}." if agent_id else "No agent_id provided."
            print(f"[create_bigquery_memory_block] {log_message} Creating a new BigQuery block.")

            # Truncate block value to 3000 characters to avoid Letta API limits
            original_value = block_data.get("value", "")
            if len(original_value) > 3000:
                truncated_value = original_value[:2950] + "\n\n[TRUNCATED - Content too long for memory block]"
                block_data["value"] = truncated_value
                print(f"[create_bigquery_memory_block] Truncated block value from {len(original_value)} to {len(truncated_value)} characters")

            blocks_url = get_api_url("blocks")
            create_response = requests.post(blocks_url, json=block_data, headers=LETTA_API_HEADERS)
            create_response.raise_for_status()
            created_block_json = create_response.json()
            
            new_block_id = created_block_json.get("id") if isinstance(created_block_json, dict) else None
            if isinstance(created_block_json, list) and created_block_json:
                 new_block_id = created_block_json[0].get("id")

            if not new_block_id:
                raise ValueError("[create_bigquery_memory_block] Critical: No block ID returned from create endpoint after creating new BigQuery block.")
            
            new_block_name = block_data.get("name")

            result = {
                "success": True, "block_id": new_block_id, "block_name": new_block_name,
                "message": f"BigQuery memory block {new_block_name} created successfully", "updated": False
            }
            
            if agent_id:
                print(f"[create_bigquery_memory_block] Attaching newly created BigQuery block {new_block_id} to agent {agent_id}.")
                attach_url = get_api_url(f"agents/{agent_id}/core-memory/blocks/attach/{new_block_id}")
                attach_headers = {**LETTA_API_HEADERS, "user_id": agent_id}
                attach_response = requests.patch(attach_url, headers=attach_headers, json={})
                attach_response.raise_for_status()
                print(f"[create_bigquery_memory_block] New BigQuery block {new_block_id} attached successfully to agent {agent_id}.")
        
        # Add agent info to the result if agent_id is present and operation was successful
        if agent_id and result.get("success"):
            # Get basic agent info
            agent_info_response = requests.get(
                get_api_url(f"agents/{agent_id}"),
                headers=LETTA_API_HEADERS
            )
            agent_info_response.raise_for_status()
            agent_info_data = agent_info_response.json()
            
            agent_name_from_api = "Unknown"
            if isinstance(agent_info_data, list) and agent_info_data:
                agent_name_from_api = agent_info_data[0].get("name", "Unknown")
            elif isinstance(agent_info_data, dict):
                agent_name_from_api = agent_info_data.get("name", "Unknown")
            
            result.update({
                "agent_id": agent_id,
                "agent_name": agent_name_from_api,
                "block_type": "bigquery"
            })
            
        return result
        
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to interact with Letta API for BigQuery block: {str(e)}")

def create_arxiv_memory_block(block_data: Dict[str, Any], agent_id: Optional[str] = None) -> Dict[str, Any]:
    """Create or update an arXiv memory block in Letta - reuses existing blocks with cumulative context."""
    try:
        print(f"[create_arxiv_memory_block] Processing arXiv block with label: {block_data.get('label')}")
        print(f"[create_arxiv_memory_block] Block name: {block_data.get('name')}")
        
        # Ensure the label is set correctly to avoid mixing with other block types
        if block_data.get("label") != "arxiv_papers":
            print(f"[create_arxiv_memory_block] WARNING: Expected label 'arxiv_papers', got '{block_data.get('label')}'. Correcting label.")
            block_data["label"] = "arxiv_papers"
        
        # Truncate block value to 3000 characters to avoid Letta API limits
        original_value = block_data.get("value", "")
        if len(original_value) > 3000:
            truncated_value = original_value[:2950] + "\n\n[TRUNCATED - Content too long for memory block]"
            block_data["value"] = truncated_value
            print(f"[create_arxiv_memory_block] Truncated block value from {len(original_value)} to {len(truncated_value)} characters")
        
        # Use the main create_memory_block function which handles finding and updating existing blocks
        # The create_memory_block function will route to find_arxiv_block based on the 'arxiv_papers' label
        result = create_memory_block(block_data, agent_id)
        
        # Add block type metadata for compatibility
        if result.get("success"):
            result["block_type"] = "arxiv_papers"
            
        return result
        
    except Exception as e:
        raise RuntimeError(f"Failed to interact with Letta API for arXiv block: {str(e)}")

def create_gdelt_memory_block(block_data: Dict[str, Any], agent_id: Optional[str] = None) -> Dict[str, Any]:
    """Create or update a GDELT memory block in Letta - reuses existing blocks with cumulative context."""
    try:
        print(f"[create_gdelt_memory_block] Processing GDELT block with label: {block_data.get('label')}")
        print(f"[create_gdelt_memory_block] Block name: {block_data.get('name')}")
        
        # Ensure the label is set correctly to avoid mixing with other block types
        if block_data.get("label") != "gdelt_news":
            print(f"[create_gdelt_memory_block] WARNING: Expected label 'gdelt_news', got '{block_data.get('label')}'. Correcting label.")
            block_data["label"] = "gdelt_news"
        
        # Truncate block value to 3000 characters to avoid Letta API limits
        original_value = block_data.get("value", "")
        if len(original_value) > 3000:
            truncated_value = original_value[:2950] + "\n\n[TRUNCATED - Content too long for memory block]"
            block_data["value"] = truncated_value
            print(f"[create_gdelt_memory_block] Truncated block value from {len(original_value)} to {len(truncated_value)} characters")
        
        # Use the main create_memory_block function which handles finding and updating existing blocks
        # Note: Currently create_memory_block doesn't have a find function for gdelt_news (always creates new)
        # but this maintains consistency and allows for future enhancement
        result = create_memory_block(block_data, agent_id)
        
        # Add block type metadata for compatibility
        if result.get("success"):
            result["block_type"] = "gdelt_news"
            
        return result
        
    except Exception as e:
        raise RuntimeError(f"Failed to interact with Letta API for GDELT block: {str(e)}")
        
        new_block_name = block_data.get("name")
        result = {
            "success": True, 
            "block_id": new_block_id, 
            "block_name": new_block_name,
            "message": f"GDELT memory block {new_block_name} created successfully", 
            "updated": False
        }
        
        # Attach to agent if provided
        if agent_id:
            print(f"[create_gdelt_memory_block] Attaching new GDELT block {new_block_id} to agent {agent_id}.")
            attach_url = get_api_url(f"agents/{agent_id}/core-memory/blocks/attach/{new_block_id}")
            attach_headers = {**LETTA_API_HEADERS, "user_id": agent_id}
            attach_response = requests.patch(attach_url, headers=attach_headers, json={})
            attach_response.raise_for_status()
            print(f"[create_gdelt_memory_block] GDELT block {new_block_id} attached successfully to agent {agent_id}.")
        
        # Add agent info to the result if agent_id is present and operation was successful
        if agent_id and result.get("success"):
            # Get basic agent info
            agent_info_response = requests.get(
                get_api_url(f"agents/{agent_id}"),
                headers=LETTA_API_HEADERS
            )
            agent_info_response.raise_for_status()
            agent_info_data = agent_info_response.json()
            
            agent_name_from_api = "Unknown"
            if isinstance(agent_info_data, list) and agent_info_data:
                agent_name_from_api = agent_info_data[0].get("name", "Unknown")
            elif isinstance(agent_info_data, dict):
                agent_name_from_api = agent_info_data.get("name", "Unknown")
            
            result.update({
                "agent_id": agent_id,
                "agent_name": agent_name_from_api,
                "block_type": "gdelt_news"
            })
            
        return result
        
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to interact with Letta API for GDELT block: {str(e)}")

def _build_cumulative_context(existing_context: str, new_context: str) -> str:
    """
    Build cumulative context by appending new context to existing context.
    Implements deduplication and truncation logic.
    """
    # Use the global constant for maximum context length
    global MAX_CONTEXT_SNIPPET_LENGTH
    
    # Create timestamp separator for new entry
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    separator = f"\n\n--- CONTEXT ENTRY ({timestamp}) ---\n\n"
    
    # Handle empty existing context
    if not existing_context or existing_context.strip() == "":
        return new_context
    
    # Handle empty new context
    if not new_context or new_context.strip() == "":
        return existing_context
    
    # Simple deduplication: check if new context is substantially similar to the most recent entry
    existing_entries = _parse_context_entries(existing_context)
    if existing_entries:
        most_recent_entry = existing_entries[-1]["content"]
        if _is_content_similar_with_query_awareness(most_recent_entry, new_context):
            print("[_build_cumulative_context] New context is similar to most recent entry, skipping append.")
            return existing_context
    
    # Build new cumulative context
    cumulative_context = existing_context + separator + new_context
    
    # Truncate if exceeds maximum length
    if len(cumulative_context) > MAX_CONTEXT_SNIPPET_LENGTH:
        cumulative_context = _truncate_oldest_entries(cumulative_context, MAX_CONTEXT_SNIPPET_LENGTH)
    
    return cumulative_context

def _parse_context_entries(context: str) -> List[Dict[str, str]]:
    """
    Parse context string into individual entries with timestamps.
    Returns list of dicts with 'timestamp' and 'content' keys.
    """
    import re
    
    # Pattern to match context entry separators
    separator_pattern = r'\n\n--- CONTEXT ENTRY \(([^)]+)\) ---\n\n'
    
    # Split by separators
    parts = re.split(separator_pattern, context)
    
    entries = []
    if len(parts) >= 1:
        # First part might be content before any separator (legacy content)
        first_part = parts[0].strip()
        if first_part:
            entries.append({
                "timestamp": "Legacy",
                "content": first_part
            })
        
        # Process pairs of (timestamp, content)
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                timestamp = parts[i]
                content = parts[i + 1].strip()
                if content:
                    entries.append({
                        "timestamp": timestamp,
                        "content": content
                    })
    
    return entries

def _is_content_similar_with_query_awareness(content1: str, content2: str) -> bool:
    """
    Check if content is similar, but with special handling for arXiv and Graphiti content
    to ensure different queries are always treated as different even if content overlaps.
    """
    if not content1 or not content2:
        return False
    
    # For arXiv content, check if the queries are different
    if "**Recent Research Papers (arXiv)**" in content1 and "**Recent Research Papers (arXiv)**" in content2:
        # Extract the query lines from both contents
        def extract_arxiv_query(content):
            lines = content.split('\n')
            for line in lines:
                if 'papers relevant to:' in line:
                    # Extract the query part after "relevant to:"
                    query_part = line.split('papers relevant to:')[-1].strip()
                    return query_part.rstrip('*').strip()
            return None
        
        query1 = extract_arxiv_query(content1)
        query2 = extract_arxiv_query(content2)
        
        if query1 and query2 and query1 != query2:
            print(f"[_is_content_similar_with_query_awareness] Different arXiv queries detected:")
            print(f"  Query 1: {query1}")
            print(f"  Query 2: {query2}")
            print(f"  Treating as different content even if papers overlap.")
            return False
        elif query1 and query2 and query1 == query2:
            print(f"[_is_content_similar_with_query_awareness] Same arXiv query detected: {query1}")
            # Fall through to regular similarity check
    
    # For Graphiti content, check if we have different context entries with timestamps
    if "Relevant Entities from Knowledge Graph:" in content1 and "Relevant Entities from Knowledge Graph:" in content2:
        # Look for timestamp patterns that indicate different search contexts
        import re
        
        # Extract timestamps from context entries
        timestamp_pattern = r'--- CONTEXT ENTRY \(([^)]+)\) ---'
        timestamps1 = re.findall(timestamp_pattern, content1)
        timestamps2 = re.findall(timestamp_pattern, content2)
        
        # If we have different timestamps, these are different searches
        if timestamps1 and timestamps2:
            latest1 = timestamps1[-1] if timestamps1 else None
            latest2 = timestamps2[-1] if timestamps2 else None
            
            if latest1 != latest2:
                print(f"[_is_content_similar_with_query_awareness] Different Graphiti search contexts detected:")
                print(f"  Latest timestamp 1: {latest1}")
                print(f"  Latest timestamp 2: {latest2}")
                print(f"  Treating as different content.")
                return False
        
        # If no timestamps found, these are likely different base contexts
        # and should be treated as different
        if not timestamps1 and not timestamps2:
            print(f"[_is_content_similar_with_query_awareness] Different Graphiti base contexts detected (no timestamps).")
            print(f"  Treating as different content.")
            return False
    
    # For non-arXiv/non-Graphiti content or same queries, use regular similarity logic
    return _is_content_similar(content1, content2)

def _is_content_similar(content1: str, content2: str) -> bool:
    """
    Simple similarity check to detect duplicate or highly similar content.
    Returns True if contents are substantially similar.
    """
    if not content1 or not content2:
        return False
    
    # Simple checks for exact or near-exact duplicates
    content1_clean = content1.strip().lower()
    content2_clean = content2.strip().lower()
    
    # Exact match
    if content1_clean == content2_clean:
        return True
    
    # Check if one is contained within the other (80% threshold)
    shorter_len = min(len(content1_clean), len(content2_clean))
    longer_len = max(len(content1_clean), len(content2_clean))
    
    if shorter_len > 0 and longer_len > 0:
        # If one is much shorter, check containment
        if shorter_len / longer_len < 0.8:
            return content1_clean in content2_clean or content2_clean in content1_clean
        
        # For similar length strings, check character overlap
        common_chars = len(set(content1_clean) & set(content2_clean))
        total_unique_chars = len(set(content1_clean) | set(content2_clean))
        
        if total_unique_chars > 0:
            similarity_ratio = common_chars / total_unique_chars
            return similarity_ratio > 0.9
    
    return False

def _truncate_oldest_entries(context: str, max_length: int) -> str:
    """
    Truncate oldest context entries to fit within max_length.
    Preserves the most recent entries.
    """
    if len(context) <= max_length:
        return context
    
    entries = _parse_context_entries(context)
    if not entries:
        # If we can't parse entries, just truncate from the beginning
        return context[-max_length:]
    
    # Start with the most recent entry and work backwards
    result_entries = []
    current_length = 0
    
    # Add a truncation notice
    truncation_notice = "--- OLDER ENTRIES TRUNCATED ---\n\n"
    
    for entry in reversed(entries):
        # Format the entry as it would appear in the final context
        if entry["timestamp"] == "Legacy":
            formatted_entry = entry["content"]
        else:
            formatted_entry = f"\n\n--- CONTEXT ENTRY ({entry['timestamp']}) ---\n\n{entry['content']}"
        
        # Check if adding this entry would exceed the limit
        proposed_length = current_length + len(formatted_entry) + len(truncation_notice)
        
        if proposed_length <= max_length:
            result_entries.insert(0, formatted_entry)
            current_length += len(formatted_entry)
        else:
            # We've hit the limit, add truncation notice if there's space
            if current_length + len(truncation_notice) <= max_length:
                result_entries.insert(0, truncation_notice.rstrip())
            break
    
    return "".join(result_entries)

# Attempt to import the context generation function and related constants
try:
    # Try to import from improved retrieval first, then fallback to original
    try:
        from production_improved_retrieval import (
            generate_context_from_prompt,
            extract_text_from_content,
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
        print("[SUCCESS] Using production improved retrieval system with semantic filtering")
    except ImportError:
        from retrieve_context import (
            generate_context_from_prompt,
            extract_text_from_content,
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
        print("[WARNING] Using basic retrieval system (improved retrieval unavailable)")
    
    from tool_manager import get_agent_tools, find_attach_tools # Import both functions
    
    # Import BigQuery GDELT integration
    try:
        from bigquery_gdelt_integration import (
            generate_bigquery_context,
            should_invoke_bigquery,
            BIGQUERY_ENABLED
        )
        print("[SUCCESS] BigQuery GDELT integration available")
    except ImportError as e:
        print(f"[WARNING] BigQuery GDELT integration unavailable: {e}")
        # Provide dummy functions
        def generate_bigquery_context(user_message: str, agent_context: Optional[str] = None) -> Optional[str]:
            return None
        def should_invoke_bigquery(user_message: str, agent_context: Optional[str] = None) -> bool:
            return False
        BIGQUERY_ENABLED = False
    
    # Import GDELT API integration
    # Check environment variable for GDELT API enablement
    gdelt_api_enabled_env = os.environ.get("GDELT_API_ENABLED", "true").lower() in ("true", "1", "yes")
    
    try:
        from demo_gdelt_webhook_integration import GDELTWebhookIntegration
        import_successful = True
        gdelt_integration = GDELTWebhookIntegration()
        if gdelt_api_enabled_env:
            print("[SUCCESS] GDELT API integration available")
        else:
            print("[WARNING] GDELT API integration disabled by GDELT_API_ENABLED environment variable")
    except ImportError as e:
        print(f"[WARNING] GDELT API integration unavailable: {e}")
        import_successful = False
        # Provide dummy class and functions
        class DummyGDELTIntegration:
            def should_trigger_gdelt_search(self, message: str) -> tuple[bool, str]:
                """
                Determine if GDELT search should be triggered based on message content.
                Returns: (should_trigger: bool, category: str)
                """
                if not message or not message.strip():
                    return False, ''
                
                message_lower = message.lower()
                
                # News and current events keywords
                news_keywords = [
                    'news', 'breaking', 'latest', 'current events', 'headlines',
                    'happening', 'today', 'recent', 'update', 'developments'
                ]
                
                # Global and political keywords
                global_keywords = [
                    'global', 'world', 'international', 'worldwide', 'country',
                    'nations', 'politics', 'political', 'government', 'diplomatic'
                ]
                
                # Crisis and conflict keywords
                crisis_keywords = [
                    'crisis', 'conflict', 'war', 'protest', 'violence', 'attack',
                    'terrorism', 'disaster', 'emergency', 'urgent'
                ]
                
                # Economic keywords
                economic_keywords = [
                    'economic', 'economy', 'market', 'financial', 'trade',
                    'stocks', 'gdp', 'inflation', 'recession'
                ]
                
                # Check for news/events triggers
                if any(keyword in message_lower for keyword in news_keywords):
                    if any(keyword in message_lower for keyword in global_keywords):
                        return True, 'global_news'
                    if any(keyword in message_lower for keyword in crisis_keywords):
                        return True, 'crisis_events'
                    return True, 'general_news'
                
                # Check for global events
                if any(keyword in message_lower for keyword in global_keywords):
                    return True, 'global_events'
                
                # Check for crisis/conflict
                if any(keyword in message_lower for keyword in crisis_keywords):
                    return True, 'crisis_events'
                
                # Check for economic events
                if any(keyword in message_lower for keyword in economic_keywords):
                    return True, 'economic_events'
                
                # Specific phrases that should trigger GDELT
                trigger_phrases = [
                    'what is happening', 'what\'s happening', 'current situation',
                    'breaking events', 'world events', 'global situation',
                    'latest developments', 'recent events'
                ]
                
                if any(phrase in message_lower for phrase in trigger_phrases):
                    return True, 'general_events'
                
                return False, ''

            def generate_gdelt_context(self, message: str, category: str) -> dict:
                return {'success': False, 'error': 'GDELT integration not available'}
        gdelt_integration = DummyGDELTIntegration()
    
    # Set GDELT_ENABLED based on both import success and environment variable
    GDELT_ENABLED = import_successful and gdelt_api_enabled_env
    
    # If import was successful but disabled by environment variable, use dummy integration
    if import_successful and not gdelt_api_enabled_env:
        class DummyGDELTIntegration:
            def should_trigger_gdelt_search(self, message: str) -> tuple[bool, str]:
                """
                Determine if GDELT search should be triggered based on message content.
                Returns: (should_trigger: bool, category: str)
                """
                if not message or not message.strip():
                    return False, ''
                
                message_lower = message.lower()
                
                # News and current events keywords
                news_keywords = [
                    'news', 'breaking', 'latest', 'current events', 'headlines',
                    'happening', 'today', 'recent', 'update', 'developments'
                ]
                
                # Global and political keywords
                global_keywords = [
                    'global', 'world', 'international', 'worldwide', 'country',
                    'nations', 'politics', 'political', 'government', 'diplomatic'
                ]
                
                # Crisis and conflict keywords
                crisis_keywords = [
                    'crisis', 'conflict', 'war', 'protest', 'violence', 'attack',
                    'terrorism', 'disaster', 'emergency', 'urgent'
                ]
                
                # Economic keywords
                economic_keywords = [
                    'economic', 'economy', 'market', 'financial', 'trade',
                    'stocks', 'gdp', 'inflation', 'recession'
                ]
                
                # Check for news/events triggers
                if any(keyword in message_lower for keyword in news_keywords):
                    if any(keyword in message_lower for keyword in global_keywords):
                        return True, 'global_news'
                    if any(keyword in message_lower for keyword in crisis_keywords):
                        return True, 'crisis_events'
                    return True, 'general_news'
                
                # Check for global events
                if any(keyword in message_lower for keyword in global_keywords):
                    return True, 'global_events'
                
                # Check for crisis/conflict
                if any(keyword in message_lower for keyword in crisis_keywords):
                    return True, 'crisis_events'
                
                # Check for economic events
                if any(keyword in message_lower for keyword in economic_keywords):
                    return True, 'economic_events'
                
                # Specific phrases that should trigger GDELT
                trigger_phrases = [
                    'what is happening', 'what\'s happening', 'current situation',
                    'breaking events', 'world events', 'global situation',
                    'latest developments', 'recent events'
                ]
                
                if any(phrase in message_lower for phrase in trigger_phrases):
                    return True, 'general_events'
                
                return False, ''

            def generate_gdelt_context(self, message: str, category: str) -> dict:
                return {'success': False, 'error': 'GDELT integration disabled by environment variable'}
        gdelt_integration = DummyGDELTIntegration()
        
except ImportError:
    print("Error: Could not import from retrieve_context.py. Make sure it's in the same directory or PYTHONPATH.")
    # Provide a dummy function and constants if import fails
    def generate_context_from_prompt(
        messages: Any, graphiti_url: str, max_nodes: int, max_facts: int, group_ids: Optional[List[str]]
    ) -> tuple[str, str, Optional[List[str]]]:
        """
        Fallback function to generate context from Graphiti when advanced retrieval is unavailable.
        """
        # Extract the actual text content for a more user-friendly fallback
        if isinstance(messages, list) and len(messages) > 0:
            if isinstance(messages[0], dict) and 'content' in messages[0]:
                content = messages[0]['content']
                if isinstance(content, list):
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            text_parts.append(item.get('text', ''))
                    extracted_text = ' '.join(text_parts)
                else:
                    extracted_text = str(content)
            else:
                extracted_text = str(messages[0])
        else:
            extracted_text = str(messages)

        print(f"[FALLBACK DEBUG] Extracted text for search: '{extracted_text}'")
        print(f"[FALLBACK DEBUG] Using max_nodes: {max_nodes}, max_facts: {max_facts}")

        # Basic query to Graphiti using correct API parameters
        try:
            # Handle empty or None graphiti_url
            if not graphiti_url:
                print(f"[FALLBACK DEBUG] Warning: Empty graphiti_url provided, using default")
                graphiti_url = "http://192.168.50.90:8001"
            
            # Use the improved Graphiti API approach with proper parameters and retry logic
            search_url_nodes = f"{graphiti_url}/search/nodes"
            search_url_facts = f"{graphiti_url}/search/facts"
            
            # Configure session with retry logic
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            # Improved nodes search payload
            nodes_payload = {
                "query": extracted_text,
                "max_nodes": max_nodes,
                "group_ids": []  # Empty list means search all groups
            }
            
            print(f"[FALLBACK DEBUG] Searching nodes at {search_url_nodes}")
            print(f"[FALLBACK DEBUG] Nodes payload: {nodes_payload}")
            
            # Search for nodes
            nodes_response = session.post(search_url_nodes, json=nodes_payload, timeout=30)
            nodes_response.raise_for_status()
            nodes_results = nodes_response.json()
            
            print(f"[FALLBACK DEBUG] Nodes results: {nodes_results}")
            
            # Search for facts with proper parameter name
            facts_payload = {
                "query": extracted_text,
                "max_facts": max_facts,
                "group_ids": []  # Empty list means search all groups
            }
            facts_response = session.post(search_url_facts, json=facts_payload, timeout=30)
            facts_response.raise_for_status()
            facts_results = facts_response.json()
            
            print(f"[FALLBACK DEBUG] Facts results: {facts_results}")
            
            # Combine results into expected format
            search_results = {
                "nodes": nodes_results.get("nodes", []) if isinstance(nodes_results, dict) else nodes_results,
                "facts": facts_results.get("facts", []) if isinstance(facts_results, dict) else facts_results
            }
            context_parts = []
            
            if "nodes" in search_results and search_results["nodes"]:
                print(f"[FALLBACK DEBUG] Processing {len(search_results['nodes'])} nodes")
                for node in search_results["nodes"]:
                    context_parts.append(f"Node: {node.get('name', 'N/A')}\nSummary: {node.get('summary', 'N/A')}")
            
            if "facts" in search_results and search_results["facts"]:
                print(f"[FALLBACK DEBUG] Processing {len(search_results['facts'])} facts")
                for fact in search_results["facts"]:
                    context_parts.append(f"Fact: {fact.get('summary', 'N/A')}")
            
            print(f"[FALLBACK DEBUG] Generated {len(context_parts)} context parts")
            
            if not context_parts:
                fallback_msg = f"No relevant information found in Graphiti for query: '{extracted_text}' (searched {max_nodes} nodes, {max_facts} facts)"
                print(f"[FALLBACK DEBUG] No context found, returning: {fallback_msg}")
                return fallback_msg, "Identity Unknown (Fallback)", group_ids
            
            final_context = "\n\n".join(context_parts)
            print(f"[FALLBACK DEBUG] Final context length: {len(final_context)} characters")
            session.close()
            return final_context, "Identity Unknown (Fallback)", group_ids
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error querying Graphiti: {e}"
            print(f"[FALLBACK DEBUG] Error: {error_msg}")
            return error_msg, "Identity Unknown (Fallback)", group_ids
        except Exception as e:
            return f"An unexpected error occurred during context generation: {e}", "Identity Unknown (Fallback)", group_ids
    
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
    DEFAULT_GRAPHITI_URL = "http://localhost:8001" # Fallback
    DEFAULT_MAX_NODES = 3
    DEFAULT_MAX_FACTS = 5
    DEFAULT_WEIGHT_LAST_MESSAGE = 0.6
    DEFAULT_WEIGHT_PREVIOUS_ASSISTANT_MESSAGE = 0.25
    DEFAULT_WEIGHT_PRIOR_USER_MESSAGE = 0.15
    ENV_WEIGHT_LAST = "GRAPHITI_WEIGHT_LAST_MESSAGE"
    ENV_WEIGHT_PREV_ASSISTANT = "GRAPHITI_WEIGHT_PREVIOUS_ASSISTANT_MESSAGE"
    ENV_WEIGHT_PRIOR_USER = "GRAPHITI_WEIGHT_PRIOR_USER_MESSAGE"
    def get_float_env_var(name: str, default: float) -> float:
        return default # Dummy implementation
    # BigQuery dummy functions
    def generate_bigquery_context(user_message: str, agent_context: Optional[str] = None) -> Optional[str]:
        return None
    def should_invoke_bigquery(user_message: str, agent_context: Optional[str] = None) -> bool:
        return False
    BIGQUERY_ENABLED = False
    
    # Tool manager dummy functions
    def get_agent_tools(agent_id: str):
        return []
    def find_attach_tools(query: str = None, agent_id: str = None, keep_tools: str = None,
                         limit: int = 5, min_score: float = 75.0, request_heartbeat: bool = False) -> str:
        return '{"success": false, "error": "Tool manager not available"}'
    
    # GDELT dummy integration
    class DummyGDELTIntegration:
        def should_trigger_gdelt_search(self, message: str) -> tuple[bool, str]:
            return False, ''
        def generate_gdelt_context(self, message: str, category: str) -> dict:
            return {'success': False, 'error': 'GDELT integration not available'}
    gdelt_integration = DummyGDELTIntegration()
    GDELT_ENABLED = False

# --- Flask App ---
app = Flask(__name__)

# --- Environment/Configuration ---
GRAPHITI_API_URL = os.environ.get("GRAPHITI_URL", DEFAULT_GRAPHITI_URL)

# Configurable context retrieval parameters
DEFAULT_MAX_NODES_ENV = int(os.environ.get("GRAPHITI_MAX_NODES", DEFAULT_MAX_NODES))
DEFAULT_MAX_FACTS_ENV = int(os.environ.get("GRAPHITI_MAX_FACTS", DEFAULT_MAX_FACTS))

# Debug: Print the environment configuration on startup
print(f"[CONFIG] GRAPHITI_MAX_NODES from env: {os.environ.get('GRAPHITI_MAX_NODES', 'NOT_SET')}")
print(f"[CONFIG] DEFAULT_MAX_NODES_ENV resolved to: {DEFAULT_MAX_NODES_ENV}")
print(f"[CONFIG] GRAPHITI_MAX_FACTS from env: {os.environ.get('GRAPHITI_MAX_FACTS', 'NOT_SET')}")
print(f"[CONFIG] DEFAULT_MAX_FACTS_ENV resolved to: {DEFAULT_MAX_FACTS_ENV}")

# External query configuration
EXTERNAL_QUERY_ENABLED = os.environ.get("EXTERNAL_QUERY_ENABLED", "true").lower() in ("true", "1", "yes")
EXTERNAL_QUERY_API_BASE_URL = os.environ.get("EXTERNAL_QUERY_API_URL", "http://192.168.50.90:5401/")
EXTERNAL_QUERY_TIMEOUT = int(os.environ.get("EXTERNAL_QUERY_TIMEOUT", "10"))

# Query refinement configuration
QUERY_REFINEMENT_ENABLED = os.environ.get("QUERY_REFINEMENT_ENABLED", "true").lower() in ("true", "1", "yes")
QUERY_REFINEMENT_TEMPERATURE = float(os.environ.get("QUERY_REFINEMENT_TEMPERATURE", "0.3"))

# Logging configuration
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
DEBUG_MODE = os.environ.get("DEBUG_MODE", "false").lower() in ("true", "1", "yes")

# --- API Endpoints ---
@app.route("/webhook/letta", methods=["POST"])
def letta_webhook_receiver():
    """
    Receives a webhook from Letta, generates context from Graphiti, and returns it.
    """
    try:
        # Log request details
        print("\n" + "="*80)
        print(f"Incoming webhook from: {request.remote_addr}")
        print(f"Headers: {dict(request.headers)}")
        print("="*80)
        
        # Check content type and get payload
        content_type = request.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            payload = request.json
        else:
            print(f"Warning: Unexpected Content-Type: {content_type}")
            try:
                payload = request.json
            except Exception as e:
                print(f"Failed to parse JSON: {e}")
                print(f"Raw data: {request.get_data(as_text=True)}")
                return jsonify({"error": "Could not parse request body as JSON"}), 400
        
        if not payload:
            return jsonify({"error": "No JSON payload received"}), 400
        
        print(f"\nParsed webhook payload: {json.dumps(payload, indent=2)}")
        
        # Handle Letta message format - be more flexible about message types
        input_for_context_generation: Any = None
        original_prompt_for_logging: str = "" # For metadata
        is_multi_message_context: bool = False

        # Attempt to process message history first
        messages_from_payload = payload.get("request", {}).get("body", {}).get("messages", [])

        if isinstance(messages_from_payload, list) and messages_from_payload:
            # Check if the last message is from user and has content (can be empty string, retrieve_context handles stripping)
            last_msg = messages_from_payload[-1]
            if isinstance(last_msg, dict) and last_msg.get("role") == "user" and last_msg.get("content") is not None:
                try:
                    input_for_context_generation = messages_from_payload[-3:] # Pass last 3 or fewer
                    content_data = last_msg.get("content", "")
                    original_prompt_for_logging = extract_text_from_content(content_data)
                    is_multi_message_context = True
                    print("[letta_webhook_receiver] Using multi-message history for context.")
                except Exception as e:
                    print(f"[letta_webhook_receiver] Error processing messages_from_payload: {str(e)}. Will attempt fallback to direct prompt.")
                    # Reset to ensure fallback is attempted
                    input_for_context_generation = None
                    is_multi_message_context = False
            else:
                print("[letta_webhook_receiver] Last message in history not valid for multi-message context. Attempting fallback.")
        else:
            print("[letta_webhook_receiver] No message history found or not a list. Attempting fallback to direct prompt.")

        # Fallback to direct prompt if multi-message context wasn't successfully set
        if not is_multi_message_context:
            direct_prompt = payload.get("prompt")
            # We allow direct_prompt to be an empty string or whitespace, retrieve_context.py will handle it.
            if direct_prompt is not None: # Check if 'prompt' key exists
                input_for_context_generation = direct_prompt
                original_prompt_for_logging = extract_text_from_content(direct_prompt)
                is_multi_message_context = False # Explicitly false
                print(f"[letta_webhook_receiver] Using direct prompt for context: '{direct_prompt}'")
            else:
                # If neither message history nor direct prompt is available
                if input_for_context_generation is None: # Ensure it wasn't somehow set before
                    print("[letta_webhook_receiver] Critical: No valid message history and no direct prompt found.")
                    return jsonify({"error": "Missing valid 'messages' array in request.body or a 'prompt' field in payload."}), 400
        
        # Extract other optional fields with environment-configurable defaults
        max_nodes = payload.get("max_nodes", DEFAULT_MAX_NODES_ENV)
        max_facts = payload.get("max_facts", DEFAULT_MAX_FACTS_ENV)
        
        # Debug: Log the actual values being used
        print(f"[DEBUG] Using max_nodes: {max_nodes} (from payload: {payload.get('max_nodes', 'NOT_SET')}, env default: {DEFAULT_MAX_NODES_ENV})")
        print(f"[DEBUG] Using max_facts: {max_facts} (from payload: {payload.get('max_facts', 'NOT_SET')}, env default: {DEFAULT_MAX_FACTS_ENV})")
        group_ids = payload.get("group_ids")  # None is fine, will search all groups
        
        # Extract agent_id from the request path early so it can be used by integrations
        agent_id = None # Initialize agent_id
        print("[AGENT_ID_EXTRACTION] Initialized agent_id to None.")

        request_data = payload.get("request", {})
        if not request_data:
            print("[AGENT_ID_EXTRACTION] 'request' object not found in payload.")
        else:
            print(f"[AGENT_ID_EXTRACTION] Found 'request' object: {request_data}")
            request_path = request_data.get("path", "")
            if not request_path:
                print("[AGENT_ID_EXTRACTION] 'path' not found in 'request' object.")
            else:
                print(f"[AGENT_ID_EXTRACTION] Found 'path': {request_path}")
                if "agents" in request_path:
                    print("[AGENT_ID_EXTRACTION] 'agents' substring found in path.")
                    parts = request_path.split("/")
                    print(f"[AGENT_ID_EXTRACTION] Path parts: {parts}")
                    try:
                        agents_index = parts.index("agents")
                        print(f"[AGENT_ID_EXTRACTION] 'agents' segment found at index: {agents_index}")
                        if len(parts) > agents_index + 1:
                            potential_agent_id = parts[agents_index + 1]
                            print(f"[AGENT_ID_EXTRACTION] Potential agent_id segment: '{potential_agent_id}'")
                            if potential_agent_id.startswith("agent-"):
                                agent_id = potential_agent_id
                                print(f"[AGENT_ID_EXTRACTION] Successfully extracted agent_id='{agent_id}'")
                            else:
                                print(f"[AGENT_ID_EXTRACTION] Segment '{potential_agent_id}' does not start with 'agent-'.")
                        else:
                            print("[AGENT_ID_EXTRACTION] Not enough segments after 'agents' to be an agent_id.")
                    except ValueError:
                        print("[AGENT_ID_EXTRACTION] 'agents' segment not found in path parts (ValueError).")
                else:
                    print("[AGENT_ID_EXTRACTION] 'agents' substring NOT found in path.")
        
        if agent_id is None: # Check final value of agent_id
            print("[AGENT_ID_EXTRACTION] Final agent_id is None. Block will be global.")
        else:
            print(f"[AGENT_ID_EXTRACTION] Final agent_id is '{agent_id}'. Block will be agent-specific.")
            # Track agent for Matrix notifications
            track_agent_and_notify(agent_id)
        
        # Generate context
        print("\n" + "="*80)
        print(f"Generating context for input: {original_prompt_for_logging}") # Log the primary prompt
        print(f"Input type for context generation: {type(input_for_context_generation)}")
        if isinstance(input_for_context_generation, list):
            print(f"Messages for context: {json.dumps(input_for_context_generation, indent=2)}")
        print("="*80)
        
        result = generate_context_from_prompt(
            messages=input_for_context_generation, # This is now Union[str, List[Dict]]
            graphiti_url=GRAPHITI_API_URL,
            max_nodes=max_nodes,
            max_facts=max_facts,
            group_ids=group_ids
        )

        # Safely unpack the result
        if isinstance(result, tuple):
            if len(result) == 3:
                context_snippet, identity_name, group_ids = result
            elif len(result) == 2:
                context_snippet, identity_name = result
                group_ids = []
            else:
                context_snippet = str(result[0]) if result else ""
                identity_name = "Unknown"
                group_ids = []
        else:
            context_snippet = str(result) if result else ""
            identity_name = "Unknown"
            group_ids = []
# --- External Query API Call ---
        if EXTERNAL_QUERY_ENABLED and original_prompt_for_logging and original_prompt_for_logging.strip():
            EXTERNAL_QUERY_API_PATH = "query/"
            EXTERNAL_QUERY_API_URL = EXTERNAL_QUERY_API_BASE_URL.rstrip('/') + '/' + EXTERNAL_QUERY_API_PATH.lstrip('/')
            log_prompt = original_prompt_for_logging[:100] + ('...' if len(original_prompt_for_logging) > 100 else '')
            print(f"\n[ExternalQuery] Querying {EXTERNAL_QUERY_API_URL} with: '{log_prompt}'")
            try:
                params = {"query": original_prompt_for_logging}
                response = requests.get(
                    EXTERNAL_QUERY_API_URL,
                    params=params,
                    timeout=EXTERNAL_QUERY_TIMEOUT
                )
                
                if response.status_code == 200:
                    # API now returns JSON with a "short_answer" field.
                    try:
                        data = response.json()
                        short_answer = data.get("short_answer")
                        
                        if short_answer and isinstance(short_answer, str) and short_answer.strip():
                            short_answer_stripped = short_answer.strip()
                            log_answer_display = short_answer_stripped[:150] + ('...' if len(short_answer_stripped) > 150 else '')
                            print(f"[ExternalQuery] Successfully retrieved and parsed JSON. Appending 'short_answer' to context. Answer (first 150 chars): {log_answer_display}")
                            context_snippet += f"\n\nExternal Query Answer:\n{short_answer_stripped}"
                        elif short_answer is None:
                            print(f"[ExternalQuery] API call successful (200) and JSON parsed, but 'short_answer' field is missing. Response JSON: {data}", file=sys.stderr)
                        else: # short_answer exists but is empty, whitespace, or not a string
                            print(f"[ExternalQuery] API call successful (200) and JSON parsed, but 'short_answer' is empty, whitespace, or not a string. Value: '{short_answer}'. Response JSON: {data}", file=sys.stderr)
                    except json.JSONDecodeError as e:
                        print(f"[ExternalQuery] API call successful (200) but failed to decode JSON response: {e}. Response text: {response.text[:500]}", file=sys.stderr)
                else: # This corresponds to 'if response.status_code == 200:'
                    # Handle non-200 responses for the GET request
                    print(f"[ExternalQuery] API call failed with status {response.status_code}. Response text: {response.text[:500]}", file=sys.stderr)
            
            except requests.exceptions.Timeout:
                print(f"[ExternalQuery] API call to {EXTERNAL_QUERY_API_URL} timed out after {EXTERNAL_QUERY_TIMEOUT} seconds.", file=sys.stderr)
            except requests.exceptions.RequestException as e:
                error_msg = f"[DBPedia] API call to {EXTERNAL_QUERY_API_URL} failed due to a network or request error: {e}"
                print(error_msg, file=sys.stderr)
            except Exception as e:  # Catch any other unexpected errors during DBPedia call
                error_msg = f"[DBPedia] An unexpected error occurred during DBPedia API call to {EXTERNAL_QUERY_API_URL}: {e}"
                print(error_msg, file=sys.stderr)
        else:
            print("[DBPedia] Skipping DBPedia call as original_prompt_for_logging is empty or whitespace.")
        # --- End DBPedia API Call ---
        
        # --- arXiv Research Papers Integration ---
        arxiv_context = ""
        arxiv_triggered = False
        arxiv_result = None
        
        if ARXIV_AVAILABLE and arxiv_integration and original_prompt_for_logging and original_prompt_for_logging.strip():
            print(f"\n[arXiv] Checking if query should trigger arXiv search...")
            try:
                arxiv_api_result = arxiv_integration.generate_arxiv_context(original_prompt_for_logging)
                
                if arxiv_api_result.get('success'):
                    arxiv_context = arxiv_api_result.get('context', '')
                    papers_found = arxiv_api_result.get('papers_found', 0)
                    confidence = arxiv_api_result.get('confidence', 0.0)
                    category = arxiv_api_result.get('category', 'unknown')
                    
                    if arxiv_context and papers_found > 0:
                        # Don't add arXiv content to main context_snippet - it gets its own memory block
                        arxiv_triggered = True
                        print(f"[arXiv] Successfully retrieved {papers_found} papers (confidence: {confidence:.2f}, category: {category})")
                        
                        # Create arXiv memory block
                        timestamp_arxiv = datetime.now(UTC)
                        arxiv_block_data = {
                            "name": f"arxiv_{timestamp_arxiv.strftime('%Y%m%d_%H%M%S')}",
                            "label": "arxiv_papers",
                            "value": arxiv_context,
                            "metadata": {
                                "type": "arxiv_research_papers",
                                "version": "1.0",
                                "original_prompt": original_prompt_for_logging,
                                "timestamp": timestamp_arxiv.isoformat(),
                                "source": "arxiv_api_integration",
                                "category": category,
                                "papers_found": papers_found,
                                "confidence": confidence,
                                "query": original_prompt_for_logging,
                                "enabled": ARXIV_AVAILABLE
                            }
                        }
                        
                        try:
                            print("\n[arXiv] Creating arXiv memory block...")
                            print(f"[arXiv] Name: {arxiv_block_data['name']}")
                            print(f"[arXiv] Label: {arxiv_block_data['label']}")
                            print(f"[arXiv] Category: {category}")
                            print(f"[arXiv] Papers found: {papers_found}")
                            if agent_id:
                                print(f"[arXiv] Agent ID: {agent_id}")
                            
                            arxiv_result = create_arxiv_memory_block(arxiv_block_data, agent_id)
                            print(f"[arXiv] arXiv memory block created successfully: {json.dumps(arxiv_result, indent=2)}")
                            
                        except Exception as e:
                            print(f"[arXiv] Error creating arXiv memory block: {str(e)}")
                            # Continue processing even if arXiv block creation fails
                            arxiv_result = {
                                "success": False,
                                "error": str(e),
                                "category": category,
                                "papers_found": papers_found,
                                "confidence": confidence,
                                "query": original_prompt_for_logging
                            }
                    else:
                        print(f"[arXiv] Search completed but no papers found (reason: {arxiv_api_result.get('reason', 'unknown')})")
                        arxiv_result = {
                            "success": False,
                            "reason": arxiv_api_result.get('reason', 'No papers found'),
                            "category": category,
                            "confidence": confidence,
                            "query": original_prompt_for_logging
                        }
                else:
                    reason = arxiv_api_result.get('reason', arxiv_api_result.get('error', 'unknown'))
                    print(f"[arXiv] Search not triggered: {reason}")
                    arxiv_result = {
                        "success": False,
                        "reason": reason,
                        "query": original_prompt_for_logging
                    }
                    
            except Exception as e:
                print(f"[arXiv] Error during arXiv search: {str(e)}")
                arxiv_result = {
                    "success": False,
                    "error": str(e),
                    "query": original_prompt_for_logging
                }
        else:
            if not ARXIV_AVAILABLE:
                print("[arXiv] arXiv integration not available")
            elif not original_prompt_for_logging or not original_prompt_for_logging.strip():
                print("[arXiv] Skipping arXiv search: no query text")
        # --- End arXiv Integration ---
        
        print("\nRetrieved Context:")
        print("-"*40)
        print(context_snippet)
        print("="*80)

        # Attempt to find and attach relevant tools
        if agent_id and original_prompt_for_logging and original_prompt_for_logging.strip():
            print(f"\n[letta_webhook_receiver] Attempting to find and attach tools for agent '{agent_id}' based on prompt: '{original_prompt_for_logging}'")
            
            # Resolve keep_tools="*" by fetching current tools
            actual_keep_tools_str = ""
            # The hardcoded keep_tools="*" in the original call implies we always want to try and preserve.
            print(f"Resolving keep_tools='*' for agent {agent_id}: Fetching current tools...")
            existing_tool_ids = get_agent_tools(agent_id) # From updated tool_manager
            
            if existing_tool_ids:
                actual_keep_tools_str = ",".join(existing_tool_ids)
                print(f"[letta_webhook_receiver] Existing tools to preserve: {actual_keep_tools_str}")
            else:
                print("[letta_webhook_receiver] No existing tools found or error fetching. No tools will be explicitly passed to keep_tools.")

            tool_attachment_result = find_attach_tools(
                query=original_prompt_for_logging,
                agent_id=agent_id,
                limit=5, # As per user request in original code
                keep_tools=actual_keep_tools_str, # Pass the resolved comma-separated string of tool IDs
                request_heartbeat=True # Attempt to make tool update immediate for the agent
            )
            print(f"[letta_webhook_receiver] Tool attachment result: {tool_attachment_result}")
        elif not agent_id:
            print("[letta_webhook_receiver] Skipping tool attachment: agent_id is None.")
        elif not original_prompt_for_logging or not original_prompt_for_logging.strip():
            print("[letta_webhook_receiver] Skipping tool attachment: original_prompt_for_logging is empty.")
        
        # Check if BigQuery should be invoked and create BigQuery memory block
        bigquery_result = None
        if original_prompt_for_logging and original_prompt_for_logging.strip():
            print(f"\n[BigQuery] Checking if BigQuery should be invoked for: '{original_prompt_for_logging[:100]}...'")
            
            if should_invoke_bigquery(original_prompt_for_logging):
                print("[BigQuery] BigQuery invocation determined necessary. Generating BigQuery context...")
                
                bigquery_context = generate_bigquery_context(original_prompt_for_logging)
                
                if bigquery_context:
                    print(f"[BigQuery] Generated BigQuery context (length: {len(bigquery_context)})")
                    
                    # Create BigQuery memory block
                    timestamp_bq = datetime.now(UTC)
                    bigquery_block_data = {
                        "name": f"bigquery_{timestamp_bq.strftime('%Y%m%d_%H%M%S')}",
                        "label": "bigquery",
                        "value": bigquery_context,
                        "metadata": {
                            "type": "bigquery_gdelt",
                            "version": "1.0",
                            "original_prompt": original_prompt_for_logging,
                            "timestamp": timestamp_bq.isoformat(),
                            "source": "gdelt_bigquery_integration",
                            "query_type": "example_3",  # Default verbose query
                            "enabled": BIGQUERY_ENABLED
                        }
                    }
                    
                    try:
                        print("\n[BigQuery] Creating BigQuery memory block...")
                        print(f"[BigQuery] Name: {bigquery_block_data['name']}")
                        print(f"[BigQuery] Label: {bigquery_block_data['label']}")
                        if agent_id:
                            print(f"[BigQuery] Agent ID: {agent_id}")
                        
                        bigquery_result = create_bigquery_memory_block(bigquery_block_data, agent_id)
                        print(f"[BigQuery] BigQuery memory block created successfully: {json.dumps(bigquery_result, indent=2)}")
                        
                    except Exception as e:
                        print(f"[BigQuery] Error creating BigQuery memory block: {str(e)}")
                        # Continue processing even if BigQuery block creation fails
                        
                else:
                    print("[BigQuery] No BigQuery context generated despite invocation determination.")
            else:
                print("[BigQuery] BigQuery invocation not needed for this query.")
        else:
            print("[BigQuery] Skipping BigQuery check: no prompt available.")
        
        # Check if GDELT should be invoked and create GDELT memory block
        gdelt_result = None
        if original_prompt_for_logging and original_prompt_for_logging.strip():
            print(f"\n[GDELT] Checking if GDELT should be invoked for: '{original_prompt_for_logging[:100]}...'")
            
            should_trigger, category = gdelt_integration.should_trigger_gdelt_search(original_prompt_for_logging)
            
            if should_trigger:
                print(f"[GDELT] GDELT invocation determined necessary for category: {category}. Generating GDELT context...")
                
                gdelt_context_result = gdelt_integration.generate_gdelt_context(original_prompt_for_logging, category)
                
                if gdelt_context_result and gdelt_context_result.get('success'):
                    gdelt_context = gdelt_context_result.get('context', '')
                    print(f"[GDELT] Generated GDELT context (length: {len(gdelt_context)})")
                    
                    # Create GDELT memory block
                    timestamp_gdelt = datetime.now(UTC)
                    gdelt_block_data = {
                        "name": f"gdelt_{timestamp_gdelt.strftime('%Y%m%d_%H%M%S')}",
                        "label": "gdelt_news",
                        "value": gdelt_context,
                        "metadata": {
                            "type": "gdelt_global_news",
                            "version": "1.0",
                            "original_prompt": original_prompt_for_logging,
                            "timestamp": timestamp_gdelt.isoformat(),
                            "source": "gdelt_api_integration",
                            "category": category,
                            "query": gdelt_context_result.get('query', ''),
                            "enabled": GDELT_ENABLED
                        }
                    }
                    
                    try:
                        print("\n[GDELT] Creating GDELT memory block...")
                        print(f"[GDELT] Name: {gdelt_block_data['name']}")
                        print(f"[GDELT] Label: {gdelt_block_data['label']}")
                        print(f"[GDELT] Category: {category}")
                        if agent_id:
                            print(f"[GDELT] Agent ID: {agent_id}")
                        
                        gdelt_result = create_gdelt_memory_block(gdelt_block_data, agent_id)
                        print(f"[GDELT] GDELT memory block created successfully: {json.dumps(gdelt_result, indent=2)}")
                        
                    except Exception as e:
                        print(f"[GDELT] Error creating GDELT memory block: {str(e)}")
                        # Continue processing even if GDELT block creation fails
                        gdelt_result = {
                            "success": False,
                            "error": str(e),
                            "category": category,
                            "query": gdelt_context_result.get('query', '')
                        }
                        
                else:
                    print("[GDELT] No GDELT context generated or generation failed.")
                    gdelt_result = {
                        "success": False,
                        "error": gdelt_context_result.get('error', 'Unknown error'),
                        "category": category,
                        "query": gdelt_context_result.get('query', '')
                    }
            else:
                print("[GDELT] GDELT invocation not needed for this query.")
        else:
            print("[GDELT] Skipping GDELT check: no prompt available.")
        
        # Prepare memory block data for context
        print(f"[letta_webhook_receiver] Length of generated context_snippet: {len(context_snippet)}")
        
        # Note: Truncation is now handled by the cumulative context system in _build_cumulative_context
        context_snippet_to_send = str(context_snippet)  # Ensure it's a string

        timestamp = datetime.now(UTC)
        block_data = {
            "name": f"graphiti_context_{timestamp.strftime('%Y%m%d_%H%M%S')}",
            "label": "graphiti_context",
            "value": context_snippet_to_send, # Use the potentially truncated version
            "metadata": {
                "type": "graphiti_context",
                "version": "1.1", # Updated version due to weighting
                "original_prompt": original_prompt_for_logging, # Log the main prompt
                "timestamp": timestamp.isoformat(),
                "source": "graphiti_weighted_search",
                "max_nodes_requested": max_nodes,
                "max_facts_requested": max_facts,
                "group_ids_requested": group_ids,
                "weighting_strategy_active": is_multi_message_context,
                "weights_configured": {
                    "last_message": get_float_env_var(ENV_WEIGHT_LAST, DEFAULT_WEIGHT_LAST_MESSAGE),
                    "previous_assistant_message": get_float_env_var(ENV_WEIGHT_PREV_ASSISTANT, DEFAULT_WEIGHT_PREVIOUS_ASSISTANT_MESSAGE),
                    "prior_user_message": get_float_env_var(ENV_WEIGHT_PRIOR_USER, DEFAULT_WEIGHT_PRIOR_USER_MESSAGE)
                }
            }
        }
        
        print("\nCreating memory block...")
        print(f"Name: {block_data['name']}")
        print(f"Label: {block_data['label']}")
        if agent_id:
            print(f"Agent ID: {agent_id}")
        
        try:
            # Create the memory block and optionally attach it to the agent
            result = create_memory_block(block_data, agent_id)
            print(f"Graphiti memory block created successfully: {json.dumps(result, indent=2)}")
            
            # Manually add identity_name to the result for the response
            if 'identity_name' not in result:
                result['identity_name'] = identity_name

            # Prepare combined response including Graphiti, BigQuery, and GDELT results
            combined_result = {
                "graphiti": result,
                "success": result.get("success", False),
                "message": result.get("message", "Memory blocks processed")
            }
            
            # Manually add identity_name to the graphiti part of the response
            if 'graphiti' in combined_result and isinstance(combined_result['graphiti'], dict):
                combined_result['graphiti']['identity_name'] = identity_name
            
            # Add BigQuery results if available
            if bigquery_result:
                combined_result["bigquery"] = bigquery_result
            else:
                combined_result["bigquery"] = None
            
            # Add GDELT results if available
            if gdelt_result:
                combined_result["gdelt"] = gdelt_result
            else:
                combined_result["gdelt"] = None
            
            # Add arXiv results if available
            if arxiv_result:
                combined_result["arxiv"] = arxiv_result
            else:
                combined_result["arxiv"] = None
            
            # Update success status and message to reflect all operations
            graphiti_success = result.get("success", False)
            bigquery_success = bigquery_result.get("success", False) if bigquery_result else None
            gdelt_success = gdelt_result.get("success", False) if gdelt_result else None
            arxiv_success = arxiv_result.get("success", False) if arxiv_result else None
            
            # Overall success is true if graphiti succeeds and no other services fail
            overall_success = graphiti_success
            if bigquery_result and not bigquery_success:
                overall_success = False
            if gdelt_result and not gdelt_success:
                overall_success = False
            if arxiv_result and not arxiv_success:
                overall_success = False
                
            combined_result["success"] = overall_success
            
            # Build detailed message
            services_status = [f"Graphiti: {graphiti_success}"]
            if bigquery_result:
                services_status.append(f"BigQuery: {bigquery_success}")
            else:
                services_status.append("BigQuery: not invoked")
            
            if gdelt_result:
                services_status.append(f"GDELT: {gdelt_success}")
            else:
                services_status.append("GDELT: not invoked")
            
            if arxiv_result and arxiv_success:
                papers_count = arxiv_result.get("papers_found", 0)
                services_status.append(f"arXiv: {papers_count} papers")
            elif arxiv_result:
                services_status.append("arXiv: no papers found")
            else:
                services_status.append("arXiv: not triggered")
                
            combined_result["message"] = f"Memory blocks processed. {', '.join(services_status)}"
            
            # Include agent info from the primary result
            for key in ["agent_id", "agent_name", "block_id", "block_name"]:
                if key in result:
                    combined_result[key] = result[key]
            
            print("="*80 + "\n")
            return jsonify(combined_result)
            
        except Exception as e:
            error_msg = f"Failed to create memory block: {str(e)}"
            print(f"Error: {error_msg}")
            print("="*80 + "\n")
            
            error_response = {
                "error": error_msg,
                "block_data": block_data,
                "agent_id": agent_id,
                "graphiti": {"success": False, "error": error_msg},
                "bigquery": bigquery_result if bigquery_result else None,
                "gdelt": gdelt_result if gdelt_result else None,
                "success": False
            }
            return jsonify(error_response), 500

    except Exception as e:
        print(f"Error processing webhook: {e}")
        return jsonify({"error": f"Failed to process webhook: {str(e)}"}), 500

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "matrix_client_url": MATRIX_CLIENT_URL
    })

@app.route("/agent-tracker/status", methods=["GET"])
def agent_tracker_status():
    """Get current status of agent tracking."""
    with agent_tracking_lock:
        return jsonify({
            "known_agents": list(known_agents),
            "agent_count": len(known_agents),
            "matrix_client_url": MATRIX_CLIENT_URL,
            "timestamp": datetime.now(UTC).isoformat()
        })

@app.route("/agent-tracker/reset", methods=["POST"])
def reset_agent_tracker():
    """Reset the agent tracking state (for testing)."""
    with agent_tracking_lock:
        old_count = len(known_agents)
        known_agents.clear()
        return jsonify({
            "message": f"Reset agent tracker. Removed {old_count} agents.",
            "timestamp": datetime.now(UTC).isoformat()
        })

# --- Main execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Graphiti Context Webhook Receiver server (Flask version).")
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Host to bind the server to."
    )
    parser.add_argument(
        "--port", type=int, default=5005, help="Port to run the server on."
    )
    parser.add_argument(
        "--debug", action="store_true", help="Run Flask in debug mode."
    )
    cli_args = parser.parse_args()

    print(f"Starting Graphiti Context Webhook Receiver (Flask) on {cli_args.host}:{cli_args.port}")
    print(f"Using Graphiti API URL: {GRAPHITI_API_URL}")
    if "Context generation system currently using basic mode" in str(generate_context_from_prompt("", GRAPHITI_API_URL, 0, 0, None)):
        print("WARNING: Running with DUMMY context generation function due to import error.")
    
    app.run(host=cli_args.host, port=cli_args.port, debug=cli_args.debug)