import argparse
import json
import os
import sys
import requests
import threading
import random
import asyncio
from datetime import datetime, UTC
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from flask import Flask, request, jsonify

from .config import get_api_url
from .memory_manager import create_memory_block  # create_tool_inventory_block REMOVED - no longer needed
from .integrations import arxiv_integration, gdelt_integration
from .context_utils import _build_cumulative_context
from .agent_registry import register_agent, query_agent_registry, format_agent_context
# from .tool_inventory import build_tool_inventory_block  # REMOVED - agents use find_tools instead

# Add the parent directory to the path to import tool_manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tool_manager import find_attach_tools
from letta_tool_utils import get_find_tools_id_with_fallback, ensure_protected_tools

app = Flask(__name__)

# Agent tracking for Matrix notifications
MATRIX_CLIENT_URL = os.environ.get("MATRIX_CLIENT_URL", "http://192.168.50.90:8004")
known_agents = set()
agent_tracking_lock = threading.Lock()

def track_agent_and_notify(agent_id: str | None) -> None:
    """Track agent and notify Matrix client if new agent is detected. Also registers agent with agent registry."""
    if not agent_id or not agent_id.startswith("agent-"):
        return
    
    with agent_tracking_lock:
        if agent_id not in known_agents:
            print(f"[AGENT_TRACKER] New agent detected: {agent_id}")
            known_agents.add(agent_id)
            
            # Background tasks for new agent
            def notify_and_register():
                # 1. Notify Matrix client
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
                
                # 2. Register with agent registry
                try:
                    print(f"[AGENT_TRACKER] Registering agent {agent_id} with agent registry...")
                    success = register_agent(agent_id)
                    if success:
                        print(f"[AGENT_TRACKER] Successfully registered agent {agent_id} with agent registry")
                    else:
                        print(f"[AGENT_TRACKER] Failed to register agent {agent_id} with agent registry")
                except Exception as e:
                    print(f"[AGENT_TRACKER] Error registering agent with registry: {e}")
            
            # Run both tasks in background to avoid blocking webhook processing
            threading.Thread(target=notify_and_register, daemon=True).start()
        else:
            print(f"[AGENT_TRACKER] Known agent: {agent_id}")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for Docker."""
    return jsonify({
        "status": "healthy", 
        "service": "webhook-server",
        "matrix_client_url": MATRIX_CLIENT_URL,
        "timestamp": datetime.now(UTC).isoformat()
    }), 200

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

# Graphiti configuration
GRAPHITI_API_URL = os.environ.get("GRAPHITI_URL", "http://192.168.50.90:8003")
DEFAULT_MAX_NODES = int(os.environ.get("GRAPHITI_MAX_NODES", "8"))
DEFAULT_MAX_FACTS = int(os.environ.get("GRAPHITI_MAX_FACTS", "20"))

import re

def resolve_agent_from_conversation(path: str) -> str | None:
    """Resolve agent_id from a /v1/conversations/{id}/messages path via the Letta API."""
    match = re.search(r'/conversations/([^/]+)', path)
    if not match:
        return None
    conv_id = match.group(1)
    try:
        from .config import get_api_url, LETTA_API_HEADERS
        url = get_api_url(f"conversations/{conv_id}")
        resp = requests.get(url, headers=LETTA_API_HEADERS, timeout=10)
        if resp.ok:
            agent_id = resp.json().get("agent_id")
            print(f"[CONV_RESOLVE] {conv_id} -> {agent_id}")
            return agent_id
        else:
            print(f"[CONV_RESOLVE] Failed for {conv_id}: HTTP {resp.status_code}")
    except Exception as e:
        print(f"[CONV_RESOLVE] Error for {conv_id}: {e}")
    return None

def extract_user_intent(prompt: str) -> str:
    """
    Extract the actual user intent from a prompt by stripping metadata prefixes.
    Handles Matrix message format, OpenCode format, and other wrapper patterns.
    """
    if not prompt:
        return ""
    
    cleaned = prompt.strip()
    
    # Strip <system-reminder> ... </system-reminder> blocks (may appear anywhere)
    cleaned = re.sub(r'<system-reminder>.*?</system-reminder>', '', cleaned, flags=re.DOTALL)
    
    # Strip Matrix prefix: [Matrix: @user:domain in Room Name]
    matrix_pattern = r'^\[Matrix:[^\]]+\]\s*'
    cleaned = re.sub(matrix_pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Strip OpenCode prefix: [MESSAGE FROM OPENCODE USER] or similar
    opencode_pattern = r'^\[MESSAGE FROM OPENCODE[^\]]*\]\s*'
    cleaned = re.sub(opencode_pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Strip response instruction blocks at the end
    response_instruction_pattern = r'---\s*RESPONSE INSTRUCTION.*$'
    cleaned = re.sub(response_instruction_pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    
    # Strip any remaining XML-like metadata tags (e.g. <context>, <instructions>)
    cleaned = re.sub(r'<[a-z_-]+>.*?</[a-z_-]+>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    
    return cleaned.strip()

def should_skip_tool_attachment(prompt: str) -> bool:
    """
    Determine if tool attachment should be skipped for trivial messages.
    Returns True if the message is too short/trivial to warrant tool search.
    """
    if not prompt:
        return True
    
    cleaned = extract_user_intent(prompt)
    
    if len(cleaned) < 10:
        return True
    
    word_count = len(cleaned.split())
    if word_count < 3:
        return True
    
    trivial_patterns = [
        r'^(hi|hello|hey|yo|sup|thanks|thank you|ok|okay|sure|yes|no|maybe|cool|nice|great|awesome|good|bye|goodbye|later|cheers)\b',
        r'^(how are you|what\'?s up|how\'?s it going)\??$',
        r'^\W*$',  # Only punctuation/whitespace
    ]
    
    cleaned_lower = cleaned.lower()
    for pattern in trivial_patterns:
        if re.match(pattern, cleaned_lower):
            return True
    
    return False

def fetch_recent_episodes(agent_id: str, last_n: int = 3) -> list:
    try:
        url = f"{GRAPHITI_API_URL}/episodes/{agent_id}"
        resp = requests.get(url, params={"last_n": last_n}, timeout=10)
        resp.raise_for_status()
        episodes = resp.json().get("episodes", [])
        print(f"[GRAPHITI] Fetched {len(episodes)} recent episodes for {agent_id}")
        return episodes
    except Exception as e:
        print(f"[GRAPHITI] Episode fetch failed for {agent_id}: {e}")
        return []


def query_graphiti_api(query: str, max_nodes: int = None, max_facts: int = None) -> dict:
    """
    Query the Graphiti search API for context with robust timeout and retry handling.
    Uses separate /search (facts) and /search/nodes endpoints.
    """
    if max_nodes is None:
        max_nodes = DEFAULT_MAX_NODES
    if max_facts is None:
        max_facts = DEFAULT_MAX_FACTS
        
    try:
        # Handle empty or None graphiti_url
        graphiti_url = GRAPHITI_API_URL
        if not graphiti_url:
            print(f"[GRAPHITI] Warning: Empty graphiti_url provided, using default")
            graphiti_url = "http://192.168.50.90:8003"
        
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
        
        print(f"[GRAPHITI] Searching with query: '{query[:100]}...'")
        
        nodes = []
        edges = []
        
        search_config = {
            "search_methods": ["fulltext", "similarity", "hipporag", "bfs"],
            "reranker": "rrf",
            "hipporag_max_hops": 2,
            "hipporag_decay": 0.85,
            "hipporag_seed_count": 10,
            "bfs_max_depth": 2,
            "bfs_beam_width": 50,
            "bfs_max_expansions": 500,
            "bfs_max_visited": 1000,
            "bfs_hub_degree_threshold": 200,
            "bfs_min_score_cutoff": 0.1
        }
        
        try:
            facts_url = f"{graphiti_url}/search"
            facts_payload = {"query": query, "max_facts": max_facts, "config": search_config}
            print(f"[GRAPHITI] Querying facts at {facts_url} with BFS+HippoRAG")
            facts_response = session.post(facts_url, json=facts_payload, timeout=30)
            facts_response.raise_for_status()
            facts_results = facts_response.json()
            edges = facts_results.get("facts", [])
            print(f"[GRAPHITI] Got {len(edges)} facts")
        except Exception as e:
            print(f"[GRAPHITI] Facts query failed: {e}")
        
        try:
            nodes_url = f"{graphiti_url}/search/nodes"
            nodes_payload = {"query": query, "max_nodes": max_nodes, "config": search_config}
            print(f"[GRAPHITI] Querying nodes at {nodes_url} with BFS+HippoRAG")
            nodes_response = session.post(nodes_url, json=nodes_payload, timeout=30)
            nodes_response.raise_for_status()
            nodes_results = nodes_response.json()
            nodes = nodes_results.get("nodes", [])
            print(f"[GRAPHITI] Got {len(nodes)} nodes")
        except Exception as e:
            print(f"[GRAPHITI] Nodes query failed: {e}")
        
        print(f"[GRAPHITI] Results: {len(nodes)} nodes, {len(edges)} edges")
        
        context_parts = []
        
        # Process nodes
        if nodes:
            nodes_to_process = nodes[:max_nodes]
            print(f"[GRAPHITI] Processing {len(nodes_to_process)} of {len(nodes)} nodes (max_nodes={max_nodes})")
            for node in nodes_to_process:
                node_name = node.get('name', 'N/A')
                node_summary = node.get('summary', 'N/A')
                context_parts.append(f"Node: {node_name}\nSummary: {node_summary}")
        
        # Process edges as facts
        if edges:
            edges_to_process = edges[:max_facts]
            print(f"[GRAPHITI] Processing {len(edges_to_process)} of {len(edges)} edges (max_facts={max_facts})")
            seen_facts = set()
            for edge in edges_to_process:
                fact_text = edge.get('fact', edge.get('name', 'N/A'))
                if fact_text not in seen_facts and fact_text != 'N/A':
                    seen_facts.add(fact_text)
                    context_parts.append(f"Fact: {fact_text}")
            
            print(f"[GRAPHITI] After deduplication: {len(seen_facts)} unique facts")
        
        if not context_parts:
            fallback_msg = f"No relevant information found in Graphiti for query: '{query}' (limit: {max_nodes})"
            print(f"[GRAPHITI] No context found: {fallback_msg}")
            return {"context": fallback_msg, "success": False}
        
        final_context = "Relevant Entities from Knowledge Graph:\n" + "\n\n".join(context_parts)
        print(f"[GRAPHITI] Generated context length: {len(final_context)} characters")
        
        # Clean up session
        session.close()
        
        return {"context": final_context, "success": True}
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Error querying Graphiti: {e}"
        print(f"[GRAPHITI] Error: {error_msg}")
        return {"context": error_msg, "success": False}
    except Exception as e:
        error_msg = f"An unexpected error occurred during Graphiti context generation: {e}"
        print(f"[GRAPHITI] Unexpected error: {error_msg}")
        return {"context": error_msg, "success": False}

def generate_context_from_prompt(prompt: str, agent_id: str) -> dict:
    cleaned_prompt = extract_user_intent(prompt)
    if not cleaned_prompt:
        cleaned_prompt = prompt

    print(f"[CONTEXT_GEN] Raw prompt: '{prompt[:100]}...'")
    print(f"[CONTEXT_GEN] Cleaned prompt: '{cleaned_prompt[:100]}...'")

    graphiti_result = query_graphiti_api(cleaned_prompt)

    episodes = fetch_recent_episodes(agent_id, last_n=3)
    if episodes:
        episode_lines = []
        for ep in episodes:
            source = ep.get("source_description", ep.get("source", "unknown"))
            content = ep.get("content", "")[:200]
            episode_lines.append(f"- [{source}] {content}")
        episode_section = "\n\nRecent Conversation Context:\n" + "\n".join(episode_lines)
        existing_context = graphiti_result.get("context", "")
        graphiti_result["context"] = existing_context + episode_section
        graphiti_result["success"] = True

    should_arxiv, arxiv_query = arxiv_integration.should_trigger_arxiv_search(prompt)
    if should_arxiv:
        arxiv_result = arxiv_integration.generate_arxiv_context(arxiv_query)
        combined_context = graphiti_result.get("context", "")
        if arxiv_result.get("context"):
            combined_context += "\n\n" + arxiv_result.get("context", "")
        return {"context": combined_context, "success": True}

    return graphiti_result

@app.route("/health", methods=["GET"])
def health_check():
    """
    A simple health check endpoint that returns a 200 OK response.
    """
    return jsonify({"status": "ok"}), 200

@app.route("/webhook", methods=["POST"])
@app.route("/webhook/letta", methods=["POST"])
def webhook_receiver():
    """
    Receives webhooks from Letta, generates context, and returns it.
    Supports both /webhook and /webhook/letta endpoints for compatibility.
    """
    try:
        data = request.json
        
        # DEBUG: Log the incoming webhook data
        print(f"\n[WEBHOOK_DEBUG] Received webhook data:")
        print(f"[WEBHOOK_DEBUG] Full JSON: {json.dumps(data, indent=2)}")
        
        event_type = data.get("type")
        agent_id = None
        prompt = None

        if event_type in ("message_sent", "stream_started"):
            prompt = data.get("prompt")
            if not prompt and data.get("request") and data["request"].get("body"):
                prompt = data["request"]["body"].get("input", "")
            
            if data.get("response"):
                agent_id = data["response"].get("agent_id")
            
            if not agent_id and data.get("request") and data["request"].get("path"):
                path = data["request"]["path"]
                if "/agents/" in path:
                    path_parts = path.split("/")
                    if "agents" in path_parts:
                        agent_idx = path_parts.index("agents") + 1
                        if agent_idx < len(path_parts):
                            potential_agent_id = path_parts[agent_idx]
                            if potential_agent_id.startswith("agent-"):
                                agent_id = potential_agent_id
                elif "/conversations/" in path:
                    agent_id = resolve_agent_from_conversation(path)

        # Extract text from prompt if it's a list of objects
        if isinstance(prompt, list):
            prompt_text = ""
            for item in prompt:
                if isinstance(item, dict) and item.get("type") == "text":
                    prompt_text += item.get("text", "") + " "
            prompt = prompt_text.strip()

        # DEBUG: Log extracted values
        print(f"[WEBHOOK_DEBUG] Extracted values:")
        print(f"[WEBHOOK_DEBUG]   Event type: {event_type}")
        print(f"[WEBHOOK_DEBUG]   Agent ID: {agent_id}")
        print(f"[WEBHOOK_DEBUG]   Prompt: {prompt}")
        
        # Track agent for Matrix notifications
        if agent_id:
            track_agent_and_notify(agent_id)

        if not agent_id or not prompt:
            print(f"[WEBHOOK_DEBUG] Missing agent_id or prompt - returning 400")
            return jsonify({"error": "Could not extract agent_id or prompt from webhook."}), 400

        # Generate context based on the prompt
        context_result = generate_context_from_prompt(prompt, agent_id)
        
        # Create or update the memory block with the new context (agent-specific)
        block_data = {
            "label": f"graphiti_context_{agent_id}",
            "value": context_result.get("context", ""),
            "metadata": {"source": "webhook", "event_type": event_type}
        }
        create_memory_block(block_data, agent_id)

        # Agent discovery - find relevant agents for collaboration
        try:
            print(f"[AGENT_DISCOVERY] Searching for relevant agents for prompt: '{prompt[:100]}...'")
            agent_results = query_agent_registry(query=prompt, limit=10, min_score=0.3)
            
            if agent_results.get("success") and agent_results.get("agents"):
                # Create memory block with available agents
                agent_context = format_agent_context(agent_results)
                print(f"[AGENT_DISCOVERY] Formatted agent context ({len(agent_context)} chars)")
                agent_block_data = {
                    "label": f"available_agents_{agent_id}",
                    "value": agent_context,
                    "metadata": {"source": "agent_registry", "event_type": event_type}
                }
                print(f"[AGENT_DISCOVERY] Creating available_agents_{agent_id} memory block for agent {agent_id}")
                try:
                    block_result = create_memory_block(agent_block_data, agent_id)
                    print(f"[AGENT_DISCOVERY] Block creation result: {block_result.get('id') if block_result else 'None'}")
                except Exception as block_err:
                    print(f"[AGENT_DISCOVERY] Error creating block: {block_err}")
                print(f"[AGENT_DISCOVERY] Found {len(agent_results['agents'])} relevant agents")
            else:
                print(f"[AGENT_DISCOVERY] No relevant agents found or query failed")
        except Exception as e:
            print(f"[AGENT_DISCOVERY] Error during agent discovery: {e}")
            # Don't fail the whole webhook if agent discovery fails

        # Auto tool attachment - find and attach relevant tools based on the prompt
        tool_attachment_data = None
        
        if should_skip_tool_attachment(prompt):
            print(f"[AUTO_TOOL_ATTACHMENT] Skipping - trivial message detected")
        else:
            try:
                cleaned_prompt = extract_user_intent(prompt)
                print(f"[AUTO_TOOL_ATTACHMENT] Searching for tools with cleaned prompt: '{cleaned_prompt[:100]}...'")
                
                find_tools_id = get_find_tools_id_with_fallback(agent_id=agent_id)
                keep_tools_list = ["*", find_tools_id]
                keep_tools_str = ",".join(keep_tools_list)
                
                from .config import TOOL_ATTACHMENT_MIN_SCORE, TOOL_ATTACHMENT_LIMIT
                
                tool_attachment_data = find_attach_tools(
                    query=cleaned_prompt,
                    agent_id=agent_id,
                    keep_tools=keep_tools_str,
                    limit=TOOL_ATTACHMENT_LIMIT,
                    min_score=TOOL_ATTACHMENT_MIN_SCORE,
                    request_heartbeat=False,
                    return_structured=True
                )
                print(f"[AUTO_TOOL_ATTACHMENT] Tool attachment result: {tool_attachment_data}")
            except Exception as e:
                print(f"[AUTO_TOOL_ATTACHMENT] Error during tool attachment: {e}")
            # Don't fail the whole webhook if tool attachment fails
        
        # REMOVED: Tool inventory memory block - no longer needed
        # Agents can now discover available tools via find_tools protected tool
        # try:
        #     print(f"[TOOL_INVENTORY] Building tool inventory for agent {agent_id}")
        #     inventory_result = build_tool_inventory_block(
        #         agent_id=agent_id,
        #         prompt=prompt,
        #         attachment_result=tool_attachment_data
        #     )
        #     
        #     if inventory_result.get("success"):
        #         inventory_content = inventory_result.get("content", "")
        #         print(f"[TOOL_INVENTORY] Generated inventory ({len(inventory_content)} chars)")
        #         
        #         # Create/update the tool inventory memory block
        #         inventory_block = create_tool_inventory_block(agent_id, inventory_content)
        #         print(f"[TOOL_INVENTORY] Block updated: {inventory_block.get('id')}")
        #     else:
        #         error = inventory_result.get("error", "Unknown error")
        #         print(f"[TOOL_INVENTORY] Failed to build inventory: {error}")
        # except Exception as e:
        #     print(f"[TOOL_INVENTORY] Error updating tool inventory: {e}")
        #     # Don't fail the whole webhook if inventory update fails


        return jsonify({"status": "success", "message": "Context processed and tools attached"}), 200

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flask Webhook Receiver")
    parser.add_argument("--host", default="0.0.0.0", help="Hostname to bind to")
    parser.add_argument("--port", type=int, default=5005, help="Port to listen on")
    args = parser.parse_args()

    app.run(host=args.host, port=args.port)