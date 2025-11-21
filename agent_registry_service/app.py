"""
Agent Registry Service

A Flask-based service for registering and discovering Letta agents using
semantic search with Weaviate vector database.

Endpoints:
- POST /api/v1/agents/register - Register a new agent
- GET /api/v1/agents/search - Search for agents by capabilities
- GET /api/v1/agents/{agent_id} - Get agent details
- PUT /api/v1/agents/{agent_id}/status - Update agent status
- DELETE /api/v1/agents/{agent_id} - Deregister an agent
"""

import os
import sys
from datetime import datetime, UTC
from typing import Optional, List, Dict, Any

from flask import Flask, request, jsonify
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import Filter
from sentence_transformers import SentenceTransformer

# Configuration
WEAVIATE_URL = os.environ.get("WEAVIATE_URL", "http://192.168.50.90:8080")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
COLLECTION_NAME = "Agent"

# Initialize Flask app
app = Flask(__name__)

# Global variables for Weaviate client and embedding model
weaviate_client = None
embedding_model = None


def init_weaviate_client():
    """Initialize Weaviate client and create Agent collection if needed."""
    global weaviate_client
    
    try:
        print(f"[REGISTRY] Connecting to Weaviate at {WEAVIATE_URL}")
        weaviate_client = weaviate.connect_to_custom(
            http_host=WEAVIATE_URL.replace("http://", "").replace("https://", "").split(":")[0],
            http_port=int(WEAVIATE_URL.split(":")[-1]) if ":" in WEAVIATE_URL.split("//")[-1] else 8080,
            http_secure=False,
            grpc_host=WEAVIATE_URL.replace("http://", "").replace("https://", "").split(":")[0],
            grpc_port=50051,
            grpc_secure=False
        )
        
        # Check if collection exists, create if not
        if not weaviate_client.collections.exists(COLLECTION_NAME):
            print(f"[REGISTRY] Creating {COLLECTION_NAME} collection")
            weaviate_client.collections.create(
                name=COLLECTION_NAME,
                properties=[
                    Property(name="agent_id", data_type=DataType.TEXT),
                    Property(name="name", data_type=DataType.TEXT),
                    Property(name="description", data_type=DataType.TEXT),
                    Property(name="capabilities", data_type=DataType.TEXT_ARRAY),
                    Property(name="status", data_type=DataType.TEXT),
                    Property(name="tags", data_type=DataType.TEXT_ARRAY),
                    Property(name="created_at", data_type=DataType.DATE),
                    Property(name="updated_at", data_type=DataType.DATE),
                ],
                vectorizer_config=Configure.Vectorizer.none()  # We'll provide our own vectors
            )
            print(f"[REGISTRY] {COLLECTION_NAME} collection created successfully")
        else:
            print(f"[REGISTRY] {COLLECTION_NAME} collection already exists")
        
        return True
        
    except Exception as e:
        print(f"[REGISTRY] Error initializing Weaviate: {e}")
        return False


def init_embedding_model():
    """Initialize sentence-transformers embedding model."""
    global embedding_model
    
    try:
        print(f"[REGISTRY] Loading embedding model: {EMBEDDING_MODEL}")
        embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        print(f"[REGISTRY] Embedding model loaded successfully")
        return True
    except Exception as e:
        print(f"[REGISTRY] Error loading embedding model: {e}")
        return False


def generate_embedding(text: str) -> List[float]:
    """Generate embedding vector for text."""
    if embedding_model is None:
        raise RuntimeError("Embedding model not initialized")
    
    return embedding_model.encode(text).tolist()


def format_agent_for_response(agent_obj) -> Dict[str, Any]:
    """Format Weaviate agent object for API response."""
    properties = agent_obj.properties
    return {
        "agent_id": properties.get("agent_id"),
        "name": properties.get("name"),
        "description": properties.get("description"),
        "capabilities": properties.get("capabilities", []),
        "status": properties.get("status"),
        "tags": properties.get("tags", []),
        "created_at": properties.get("created_at"),
        "updated_at": properties.get("updated_at"),
    }


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    weaviate_status = "connected" if weaviate_client else "disconnected"
    embedding_status = "loaded" if embedding_model else "not loaded"
    
    return jsonify({
        "status": "healthy" if weaviate_client and embedding_model else "degraded",
        "service": "agent-registry",
        "weaviate": weaviate_status,
        "embedding_model": embedding_status,
        "timestamp": datetime.now(UTC).isoformat()
    }), 200


@app.route("/api/v1/agents/register", methods=["POST"])
def register_agent():
    """
    Register a new agent in the registry.
    
    Request body:
    {
        "agent_id": "agent-xxx",
        "name": "Agent Name",
        "description": "Agent description",
        "capabilities": ["capability1", "capability2"],
        "status": "active",
        "tags": [],
        "created_at": "ISO timestamp",
        "updated_at": "ISO timestamp"
    }
    """
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ["agent_id", "name", "description"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        agent_id = data["agent_id"]
        
        # Check if agent already exists
        collection = weaviate_client.collections.get(COLLECTION_NAME)
        existing = collection.query.fetch_objects(
            filters=Filter.by_property("agent_id").equal(agent_id),
            limit=1
        )
        
        if len(existing.objects) > 0:
            return jsonify({
                "error": f"Agent {agent_id} already registered",
                "agent_id": agent_id
            }), 409
        
        # Generate embedding from description + capabilities
        capabilities_text = " ".join(data.get("capabilities", []))
        embedding_text = f"{data['description']} {capabilities_text}"
        embedding = generate_embedding(embedding_text)
        
        # Prepare agent data
        agent_data = {
            "agent_id": agent_id,
            "name": data["name"],
            "description": data["description"],
            "capabilities": data.get("capabilities", []),
            "status": data.get("status", "active"),
            "tags": data.get("tags", []),
            "created_at": data.get("created_at", datetime.now(UTC).isoformat()),
            "updated_at": data.get("updated_at", datetime.now(UTC).isoformat()),
        }
        
        # Insert into Weaviate
        uuid = collection.data.insert(
            properties=agent_data,
            vector=embedding
        )
        
        print(f"[REGISTRY] Registered agent: {agent_id} (UUID: {uuid})")
        
        return jsonify({
            "success": True,
            "agent_id": agent_id,
            "uuid": str(uuid),
            "message": f"Agent {agent_id} registered successfully"
        }), 201
        
    except Exception as e:
        print(f"[REGISTRY] Error registering agent: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/agents/search", methods=["GET"])
def search_agents():
    """
    Search for agents using semantic search.
    
    Query parameters:
    - query: Search query text
    - limit: Maximum number of results (default: 10)
    - min_score: Minimum similarity score 0-1 (default: 0.5)
    """
    try:
        query = request.args.get("query")
        limit = int(request.args.get("limit", 10))
        min_score = float(request.args.get("min_score", 0.5))
        
        if not query:
            return jsonify({"error": "Missing required parameter: query"}), 400
        
        # Generate query embedding
        query_embedding = generate_embedding(query)
        
        # Search Weaviate
        collection = weaviate_client.collections.get(COLLECTION_NAME)
        results = collection.query.near_vector(
            near_vector=query_embedding,
            limit=limit,
            return_metadata=["distance"]
        )
        
        # Filter by min_score and format results
        agents = []
        for obj in results.objects:
            # Convert distance to similarity score (0-1)
            # Weaviate uses cosine distance, so similarity = 1 - distance
            similarity = 1 - obj.metadata.distance
            
            if similarity >= min_score:
                agent_data = format_agent_for_response(obj)
                agent_data["score"] = similarity
                agents.append(agent_data)
        
        print(f"[REGISTRY] Search query: '{query[:100]}' - Found {len(agents)} agents (min_score: {min_score})")
        
        return jsonify({
            "success": True,
            "agents": agents,
            "count": len(agents),
            "query": query
        }), 200
        
    except Exception as e:
        print(f"[REGISTRY] Error searching agents: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/agents/<agent_id>", methods=["GET"])
def get_agent(agent_id: str):
    """Get details for a specific agent."""
    try:
        collection = weaviate_client.collections.get(COLLECTION_NAME)
        results = collection.query.fetch_objects(
            filters=Filter.by_property("agent_id").equal(agent_id),
            limit=1
        )
        
        if len(results.objects) == 0:
            return jsonify({"error": f"Agent {agent_id} not found"}), 404
        
        agent_data = format_agent_for_response(results.objects[0])
        
        return jsonify({
            "success": True,
            "agent": agent_data
        }), 200
        
    except Exception as e:
        print(f"[REGISTRY] Error getting agent {agent_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/agents/<agent_id>/status", methods=["PUT"])
def update_agent_status(agent_id: str):
    """
    Update agent status.
    
    Request body:
    {
        "status": "active" | "inactive" | "offline"
    }
    """
    try:
        data = request.json
        
        if "status" not in data:
            return jsonify({"error": "Missing required field: status"}), 400
        
        new_status = data["status"]
        
        # Find agent
        collection = weaviate_client.collections.get(COLLECTION_NAME)
        results = collection.query.fetch_objects(
            filters=Filter.by_property("agent_id").equal(agent_id),
            limit=1
        )
        
        if len(results.objects) == 0:
            return jsonify({"error": f"Agent {agent_id} not found"}), 404
        
        agent_uuid = results.objects[0].uuid
        
        # Update status and updated_at
        collection.data.update(
            uuid=agent_uuid,
            properties={
                "status": new_status,
                "updated_at": datetime.now(UTC).isoformat()
            }
        )
        
        print(f"[REGISTRY] Updated agent {agent_id} status to: {new_status}")
        
        return jsonify({
            "success": True,
            "agent_id": agent_id,
            "status": new_status,
            "message": f"Agent {agent_id} status updated successfully"
        }), 200
        
    except Exception as e:
        print(f"[REGISTRY] Error updating agent {agent_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/agents/<agent_id>", methods=["DELETE"])
def delete_agent(agent_id: str):
    """Deregister an agent from the registry."""
    try:
        # Find agent
        collection = weaviate_client.collections.get(COLLECTION_NAME)
        results = collection.query.fetch_objects(
            filters=Filter.by_property("agent_id").equal(agent_id),
            limit=1
        )
        
        if len(results.objects) == 0:
            return jsonify({"error": f"Agent {agent_id} not found"}), 404
        
        agent_uuid = results.objects[0].uuid
        
        # Delete agent
        collection.data.delete_by_id(agent_uuid)
        
        print(f"[REGISTRY] Deleted agent: {agent_id}")
        
        return jsonify({
            "success": True,
            "agent_id": agent_id,
            "message": f"Agent {agent_id} deleted successfully"
        }), 200
        
    except Exception as e:
        print(f"[REGISTRY] Error deleting agent {agent_id}: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Initialize services
    print("[REGISTRY] Starting Agent Registry Service...")
    
    if not init_weaviate_client():
        print("[REGISTRY] Failed to initialize Weaviate client. Exiting.")
        sys.exit(1)
    
    if not init_embedding_model():
        print("[REGISTRY] Failed to initialize embedding model. Exiting.")
        sys.exit(1)
    
    print("[REGISTRY] Agent Registry Service initialized successfully")
    
    # Start Flask app
    port = int(os.environ.get("PORT", 8020))
    app.run(host="0.0.0.0", port=port, debug=False)
