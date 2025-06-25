#!/usr/bin/env python3
"""
Debug version of Flask webhook receiver with enhanced error logging
"""

import argparse
import json
import os
import sys
import traceback
from typing import Dict, List, Optional, Any
from datetime import datetime, UTC
import requests

from flask import Flask, request, jsonify

# Default configuration
LETTA_BASE_URL = os.environ.get("LETTA_BASE_URL", "https://letta2.oculair.ca")
LETTA_PASSWORD = os.environ.get("LETTA_PASSWORD", "lettaSecurePass123")
LETTA_API_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-BARE-PASSWORD": f"password {LETTA_PASSWORD}",
    "Authorization": f"Bearer {LETTA_PASSWORD}"
}

def get_api_url(path: str) -> str:
    """Construct API URL following Letta's v1 convention."""
    base = f"{LETTA_BASE_URL}/v1".rstrip("/")
    path = path.lstrip("/")
    return f"{base}/{path}"

# Debug function to test imports
def test_imports():
    """Test all imports to identify which ones are failing"""
    import_results = {}
    
    # Test basic imports
    try:
        import flask
        import_results['flask'] = f"✅ OK - version {flask.__version__}"
    except Exception as e:
        import_results['flask'] = f"❌ FAILED - {str(e)}"
    
    try:
        import requests
        import_results['requests'] = f"✅ OK - version {requests.__version__}"
    except Exception as e:
        import_results['requests'] = f"❌ FAILED - {str(e)}"
    
    # Test production_improved_retrieval
    try:
        from production_improved_retrieval import generate_context_from_prompt
        import_results['production_improved_retrieval'] = "✅ OK"
    except Exception as e:
        import_results['production_improved_retrieval'] = f"❌ FAILED - {str(e)}"
        # Try fallback
        try:
            from retrieve_context import generate_context_from_prompt
            import_results['retrieve_context'] = "✅ OK (fallback)"
        except Exception as e2:
            import_results['retrieve_context'] = f"❌ FAILED - {str(e2)}"
    
    # Test tool_manager
    try:
        from tool_manager import get_agent_tools, find_attach_tools
        import_results['tool_manager'] = "✅ OK"
    except Exception as e:
        import_results['tool_manager'] = f"❌ FAILED - {str(e)}"
    
    # Test cerebras client
    try:
        from llm_clients.cerebras_qwen_client import CerebrasQwenClient, CerebrasError
        import_results['cerebras_client'] = "✅ OK"
    except Exception as e:
        import_results['cerebras_client'] = f"❌ FAILED - {str(e)}"
    
    # Test sentence transformers (optional)
    try:
        from sentence_transformers import SentenceTransformer
        import_results['sentence_transformers'] = "✅ OK"
    except Exception as e:
        import_results['sentence_transformers'] = f"❌ FAILED (optional) - {str(e)}"
    
    return import_results

# Try to import all dependencies with detailed error reporting
def safe_import_dependencies():
    """Safely import dependencies with fallbacks"""
    global generate_context_from_prompt, get_agent_tools, find_attach_tools
    
    print("🔍 Testing all imports...")
    import_results = test_imports()
    
    for module, result in import_results.items():
        print(f"  {module}: {result}")
    
    # Import context generation with fallback
    try:
        from production_improved_retrieval import (
            generate_context_from_prompt,
            DEFAULT_GRAPHITI_URL,
            DEFAULT_MAX_NODES,
            DEFAULT_MAX_FACTS,
        )
        print("✅ Using production improved retrieval system")
        return True, DEFAULT_GRAPHITI_URL, DEFAULT_MAX_NODES, DEFAULT_MAX_FACTS
    except ImportError as e:
        print(f"⚠️  Production retrieval failed: {e}")
        try:
            from retrieve_context import (
                generate_context_from_prompt,
                DEFAULT_GRAPHITI_URL,
                DEFAULT_MAX_NODES,
                DEFAULT_MAX_FACTS,
            )
            print("✅ Using basic retrieval system")
            return True, DEFAULT_GRAPHITI_URL, DEFAULT_MAX_NODES, DEFAULT_MAX_FACTS
        except ImportError as e2:
            print(f"❌ Both retrieval systems failed: {e2}")
            # Create dummy function
            def generate_context_from_prompt(messages, graphiti_url, max_nodes, max_facts, group_ids):
                return f"ERROR: Context generation unavailable. Import errors: {e}, {e2}"
            
            return False, "http://localhost:8001/api", 3, 5

def safe_import_tools():
    """Safely import tool manager with fallback"""
    global get_agent_tools, find_attach_tools
    
    try:
        from tool_manager import get_agent_tools, find_attach_tools
        print("✅ Tool manager imported successfully")
        return True
    except ImportError as e:
        print(f"⚠️  Tool manager import failed: {e}")
        # Create dummy functions
        def get_agent_tools(agent_id):
            return []
        
        def find_attach_tools(query, agent_id, limit, keep_tools, request_heartbeat):
            return {"error": f"Tool manager unavailable: {e}"}
        
        return False

# Initialize imports
CONTEXT_AVAILABLE, DEFAULT_GRAPHITI_URL, DEFAULT_MAX_NODES, DEFAULT_MAX_FACTS = safe_import_dependencies()
TOOLS_AVAILABLE = safe_import_tools()

# --- Flask App ---
app = Flask(__name__)

# --- Environment/Configuration ---
GRAPHITI_API_URL = os.environ.get("GRAPHITI_URL", DEFAULT_GRAPHITI_URL)
DEFAULT_MAX_NODES_ENV = int(os.environ.get("GRAPHITI_MAX_NODES", DEFAULT_MAX_NODES))
DEFAULT_MAX_FACTS_ENV = int(os.environ.get("GRAPHITI_MAX_FACTS", DEFAULT_MAX_FACTS))

print(f"🔧 Configuration:")
print(f"   GRAPHITI_API_URL: {GRAPHITI_API_URL}")
print(f"   DEFAULT_MAX_NODES_ENV: {DEFAULT_MAX_NODES_ENV}")
print(f"   DEFAULT_MAX_FACTS_ENV: {DEFAULT_MAX_FACTS_ENV}")
print(f"   LETTA_BASE_URL: {LETTA_BASE_URL}")

@app.route("/webhook/letta", methods=["POST"])
def letta_webhook_receiver():
    """
    Debug version of webhook receiver with enhanced error logging
    """
    try:
        print("\n" + "="*80)
        print(f"🚀 Incoming webhook from: {request.remote_addr}")
        print(f"📋 Headers: {dict(request.headers)}")
        
        # Check content type and get payload
        content_type = request.headers.get('Content-Type', '')
        print(f"📝 Content-Type: {content_type}")
        
        if 'application/json' in content_type:
            payload = request.json
        else:
            print(f"⚠️  Unexpected Content-Type: {content_type}")
            try:
                payload = request.json
            except Exception as e:
                print(f"❌ Failed to parse JSON: {e}")
                print(f"📄 Raw data: {request.get_data(as_text=True)}")
                return jsonify({"error": "Could not parse request body as JSON", "details": str(e)}), 400
        
        if not payload:
            return jsonify({"error": "No JSON payload received"}), 400
        
        print(f"📦 Parsed webhook payload: {json.dumps(payload, indent=2)}")
        
        # Simple context generation for debugging
        if not CONTEXT_AVAILABLE:
            print("❌ Context generation not available")
            return jsonify({
                "error": "Context generation unavailable", 
                "import_status": test_imports(),
                "message": "Check server logs for import errors"
            }), 500
        
        # Extract prompt for testing
        messages_from_payload = payload.get("request", {}).get("body", {}).get("messages", [])
        direct_prompt = payload.get("prompt", "")
        
        if messages_from_payload:
            test_prompt = str(messages_from_payload[-1].get("content", "")) if messages_from_payload else ""
        else:
            test_prompt = direct_prompt
        
        print(f"🔍 Test prompt: {test_prompt[:100]}...")
        
        # Try context generation
        print("🧠 Attempting context generation...")
        context_snippet = generate_context_from_prompt(
            messages=test_prompt,
            graphiti_url=GRAPHITI_API_URL,
            max_nodes=2,  # Use minimal values for testing
            max_facts=3,
            group_ids=None
        )
        
        print(f"✅ Context generated successfully: {len(context_snippet)} characters")
        
        # Return minimal response for debugging
        return jsonify({
            "success": True,
            "context_length": len(context_snippet),
            "context_preview": context_snippet[:200] + "..." if len(context_snippet) > 200 else context_snippet,
            "import_status": "OK",
            "message": "Debug webhook processed successfully"
        })
        
    except Exception as e:
        error_details = {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "import_status": test_imports(),
            "environment": {
                "GRAPHITI_URL": os.environ.get("GRAPHITI_URL", "NOT_SET"),
                "LETTA_BASE_URL": os.environ.get("LETTA_BASE_URL", "NOT_SET"),
                "CEREBRAS_API_KEY": "SET" if os.environ.get("CEREBRAS_API_KEY") else "NOT_SET"
            }
        }
        
        print(f"❌ ERROR in webhook processing:")
        print(f"   Error: {str(e)}")
        print(f"   Type: {type(e).__name__}")
        print(f"   Traceback:")
        print(traceback.format_exc())
        
        return jsonify(error_details), 500

@app.route("/health", methods=["GET"])
def health_check():
    """Enhanced health check with import status"""
    import_status = test_imports()
    all_imports_ok = all("✅" in status for status in import_status.values() if "optional" not in status)
    
    return jsonify({
        "status": "healthy" if all_imports_ok else "degraded",
        "imports": import_status,
        "environment": {
            "GRAPHITI_URL": os.environ.get("GRAPHITI_URL", "NOT_SET"),
            "LETTA_BASE_URL": os.environ.get("LETTA_BASE_URL", "NOT_SET"),
            "CEREBRAS_API_KEY": "SET" if os.environ.get("CEREBRAS_API_KEY") else "NOT_SET"
        }
    })

@app.route("/debug", methods=["GET"])
def debug_info():
    """Debug endpoint to check system status"""
    return jsonify({
        "imports": test_imports(),
        "environment": dict(os.environ),
        "configuration": {
            "GRAPHITI_API_URL": GRAPHITI_API_URL,
            "DEFAULT_MAX_NODES_ENV": DEFAULT_MAX_NODES_ENV,
            "DEFAULT_MAX_FACTS_ENV": DEFAULT_MAX_FACTS_ENV,
            "LETTA_BASE_URL": LETTA_BASE_URL
        }
    })

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Debug version of Graphiti Context Webhook Receiver")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the server to.")
    parser.add_argument("--port", type=int, default=5005, help="Port to run the server on.")
    parser.add_argument("--debug", action="store_true", help="Run Flask in debug mode.")
    cli_args = parser.parse_args()

    print(f"🚀 Starting DEBUG Graphiti Context Webhook Receiver on {cli_args.host}:{cli_args.port}")
    print(f"🔧 Using Graphiti API URL: {GRAPHITI_API_URL}")
    
    # Run import tests on startup
    print("\n" + "="*50 + " STARTUP DIAGNOSTICS " + "="*50)
    import_results = test_imports()
    for module, result in import_results.items():
        print(f"  {module}: {result}")
    print("="*120)
    
    app.run(host=cli_args.host, port=cli_args.port, debug=True)  # Always use debug mode