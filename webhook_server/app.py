import argparse
import json
import os
import sys
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from flask import Flask, request, jsonify

from .config import get_api_url
from .memory_manager import create_memory_block
from .integrations import arxiv_integration, gdelt_integration
from .context_utils import _build_cumulative_context

# Add the parent directory to the path to import tool_manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tool_manager import find_attach_tools

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for Docker."""
    return jsonify({"status": "healthy", "service": "webhook-server"}), 200

# Graphiti configuration
GRAPHITI_API_URL = os.environ.get("GRAPHITI_URL", "http://192.168.50.90:8001/api")
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
            graphiti_url = "http://192.168.50.90:8001/api"
        
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
        search_url_facts = f"{graphiti_url}/search/facts"
        
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
            for fact in search_results["facts"]:
                context_parts.append(f"Fact: {fact.get('summary', 'N/A')}")
        
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
            if data.get("response"):
                agent_id = data["response"].get("agent_id")
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

        # Auto tool attachment - find and attach relevant tools based on the prompt
        try:
            print(f"[AUTO_TOOL_ATTACHMENT] Searching for relevant tools for prompt: '{prompt[:100]}...'")
            tool_result = find_attach_tools(
                query=prompt,
                agent_id=agent_id,
                keep_tools="*",  # Keep existing tools and add relevant ones
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