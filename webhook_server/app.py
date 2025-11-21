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
from .memory_manager import create_memory_block
from .integrations import arxiv_integration, gdelt_integration
from .context_utils import _build_cumulative_context
from .agent_registry import register_agent, query_agent_registry, format_agent_context

# Add the parent directory to the path to import tool_manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tool_manager import find_attach_tools
from letta_tool_utils import get_find_tools_id_with_fallback

app = Flask(__name__)

# Agent tracking for Matrix notifications
MATRIX_CLIENT_URL = os.environ.get("MATRIX_CLIENT_URL", "http://192.168.50.90:8004")
known_agents = set()
agent_tracking_lock = threading.Lock()

def track_agent_and_notify(agent_id: str) -> None:
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

def query_graphiti_api(query: str, max_nodes: int = None, max_facts: int = None) -> dict:
    """
    Query the Graphiti API for context with robust timeout and retry handling.
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
            graphiti_url = "http://192.168.50.90:8001"
        
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
        
        # Use the improved Graphiti API approach with proper parameters
        search_url_nodes = f"{graphiti_url}/search/nodes"
        search_url_facts = f"{graphiti_url}/search"
        
        print(f"[GRAPHITI] Searching nodes at {search_url_nodes}")
        
        # Improved nodes search payload
        nodes_payload = {
            "query": query,
            "max_nodes": max_nodes,
            "group_ids": []  # Empty list means search all groups
        }
        
        # Search for nodes
        nodes_response = session.post(search_url_nodes, json=nodes_payload, timeout=30)
        nodes_response.raise_for_status()
        nodes_results = nodes_response.json()
        
        print(f"[GRAPHITI] Nodes results: {len(nodes_results.get('nodes', []))} nodes found")
        
        # Search for facts with proper parameter name
        facts_payload = {
            "query": query,
            "max_facts": max_facts,
            "group_ids": []  # Empty list means search all groups
        }
        
        facts_response = session.post(search_url_facts, json=facts_payload, timeout=30)
        facts_response.raise_for_status()
        facts_results = facts_response.json()
        
        print(f"[GRAPHITI] Facts results: {len(facts_results.get('facts', []))} facts found")
        
        # Combine results into expected format
        search_results = {
            "nodes": nodes_results.get("nodes", []) if isinstance(nodes_results, dict) else nodes_results,
            "facts": facts_results.get("facts", []) if isinstance(facts_results, dict) else facts_results
        }
        
        context_parts = []
        
        if "nodes" in search_results and search_results["nodes"]:
            print(f"[GRAPHITI] Processing {len(search_results['nodes'])} nodes")
            for node in search_results["nodes"]:
                context_parts.append(f"Node: {node.get('name', 'N/A')}\nSummary: {node.get('summary', 'N/A')}")
        
        if "facts" in search_results and search_results["facts"]:
            print(f"[GRAPHITI] Processing {len(search_results['facts'])} facts")
            # Deduplicate facts by text content
            seen_facts = set()
            unique_facts = []
            for fact in search_results["facts"]:
                fact_text = fact.get('fact', 'N/A')
                if fact_text not in seen_facts and fact_text != 'N/A':
                    seen_facts.add(fact_text)
                    unique_facts.append(fact_text)
            
            print(f"[GRAPHITI] After deduplication: {len(unique_facts)} unique facts")
            for fact_text in unique_facts:
                context_parts.append(f"Fact: {fact_text}")
        
        if not context_parts:
            fallback_msg = f"No relevant information found in Graphiti for query: '{query}' (searched {max_nodes} nodes, {max_facts} facts)"
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
    """
    Generates context from a prompt, handling Graphiti, arXiv and GDELT searches.
    """
    # Start with Graphiti search
    graphiti_result = query_graphiti_api(prompt)
    
    # Check for arXiv trigger
    should_arxiv, arxiv_query = arxiv_integration.should_trigger_arxiv_search(prompt)
    if should_arxiv:
        # Fix: ArxivIntegration.generate_arxiv_context() only takes 1 argument (query)
        arxiv_result = arxiv_integration.generate_arxiv_context(arxiv_query)
        # Combine with Graphiti results if available
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

        if event_type == "message_sent":
            prompt = data.get("prompt")
            # Try to get agent_id from response first
            if data.get("response"):
                agent_id = data["response"].get("agent_id")
            # If not found, try to extract from request path
            if not agent_id and data.get("request") and data["request"].get("path"):
                path = data["request"]["path"]
                if "/agents/" in path:
                    # Extract agent_id from path like /v1/agents/agent-xxx/messages
                    path_parts = path.split("/")
                    if "agents" in path_parts:
                        agent_idx = path_parts.index("agents") + 1
                        if agent_idx < len(path_parts):
                            potential_agent_id = path_parts[agent_idx]
                            if potential_agent_id.startswith("agent-"):
                                agent_id = potential_agent_id
        elif event_type == "stream_started":
            prompt = data.get("prompt")
            if data.get("request") and data["request"].get("path"):
                path_parts = data["request"]["path"].split("/")
                if "agents" in path_parts:
                    agent_id_index = path_parts.index("agents") + 1
                    if agent_id_index < len(path_parts):
                        agent_id = path_parts[agent_id_index]

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
        
        # Create or update the memory block with the new context
        block_data = {
            "label": "graphiti_context",
            "value": context_result.get("context", ""),
            "metadata": {"source": "webhook", "event_type": event_type}
        }
        create_memory_block(block_data, agent_id)

        # Agent discovery - find relevant agents for collaboration
        try:
            print(f"[AGENT_DISCOVERY] Searching for relevant agents for prompt: '{prompt[:100]}...'")
            agent_results = query_agent_registry(query=prompt, limit=5, min_score=0.5)
            
            if agent_results.get("success") and agent_results.get("agents"):
                # Create memory block with available agents
                agent_context = format_agent_context(agent_results)
                agent_block_data = {
                    "label": "available_agents",
                    "value": agent_context,
                    "metadata": {"source": "agent_registry", "event_type": event_type}
                }
                create_memory_block(agent_block_data, agent_id)
                print(f"[AGENT_DISCOVERY] Found {len(agent_results['agents'])} relevant agents")
            else:
                print(f"[AGENT_DISCOVERY] No relevant agents found or query failed")
        except Exception as e:
            print(f"[AGENT_DISCOVERY] Error during agent discovery: {e}")
            # Don't fail the whole webhook if agent discovery fails

        # Auto tool attachment - find and attach relevant tools based on the prompt
        try:
            print(f"[AUTO_TOOL_ATTACHMENT] Searching for relevant tools for prompt: '{prompt[:100]}...'")
            
            # Dynamically lookup the find_tools tool ID using the agent's attached tools
            # Keep existing tools with "*" and add the dynamically found tool ID
            find_tools_id = get_find_tools_id_with_fallback(agent_id=agent_id)
            keep_tools_list = ["*", find_tools_id]
            keep_tools_str = ",".join(keep_tools_list)
            
            tool_result = find_attach_tools(
                query=prompt,
                agent_id=agent_id,
                keep_tools=keep_tools_str,  # Keep existing tools and specific required tool
                limit=3,  # Limit to 3 new tools to avoid overwhelming
                min_score=70.0,  # Slightly lower threshold for relevance
                request_heartbeat=False
            )
            print(f"[AUTO_TOOL_ATTACHMENT] Tool attachment result: {tool_result}")
        except Exception as e:
            print(f"[AUTO_TOOL_ATTACHMENT] Error during tool attachment: {e}")
            # Don't fail the whole webhook if tool attachment fails

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