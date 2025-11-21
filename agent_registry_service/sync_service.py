"""
Agent Registry Sync Service

Periodically syncs agents from Letta API to the Weaviate agent registry.
This ensures the registry is always up-to-date with all available agents.
"""

import os
import sys
import time
import json
import logging
import requests
from datetime import datetime, timezone
from typing import List, Dict, Any
from ollama_embeddings import OllamaEmbeddingProvider
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import Filter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment
LETTA_BASE_URL = os.environ.get("LETTA_BASE_URL", "https://letta2.oculair.ca")
LETTA_PASSWORD = os.environ.get("LETTA_PASSWORD", "")
WEAVIATE_URL = os.environ.get("WEAVIATE_URL", "http://weaviate:8080")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://192.168.50.80:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_EMBEDDING_MODEL", "dengcao/Qwen3-Embedding-4B:Q4_K_M")
EMBEDDING_DIMENSION = int(os.environ.get("EMBEDDING_DIMENSION", "2560"))
SYNC_INTERVAL = int(os.environ.get("SYNC_INTERVAL", "300"))  # Default: 5 minutes
COLLECTION_NAME = "Agent"

# Global variables
weaviate_client = None
embedding_provider = None


def init_weaviate_client():
    """Initialize Weaviate client and ensure Agent collection exists."""
    global weaviate_client
    
    try:
        logger.info(f"Connecting to Weaviate at {WEAVIATE_URL}")
        weaviate_client = weaviate.connect_to_custom(
            http_host=WEAVIATE_URL.replace("http://", "").replace("https://", "").split(":")[0],
            http_port=int(WEAVIATE_URL.split(":")[-1]) if ":" in WEAVIATE_URL.split("//")[-1] else 8080,
            http_secure=False,
            grpc_host=WEAVIATE_URL.replace("http://", "").replace("https://", "").split(":")[0],
            grpc_port=50051,
            grpc_secure=False
        )
        
        # Ensure collection exists
        if not weaviate_client.collections.exists(COLLECTION_NAME):
            logger.info(f"Creating {COLLECTION_NAME} collection")
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
                vectorizer_config=Configure.Vectorizer.none()
            )
            logger.info(f"{COLLECTION_NAME} collection created")
        
        return True
    except Exception as e:
        logger.error(f"Error initializing Weaviate: {e}")
        return False


def init_embedding_provider():
    """Initialize Ollama embedding provider."""
    global embedding_provider
    
    try:
        logger.info(f"Initializing Ollama embedding provider")
        embedding_provider = OllamaEmbeddingProvider(
            base_url=OLLAMA_BASE_URL,
            model=OLLAMA_MODEL,
            dimensions=EMBEDDING_DIMENSION
        )
        logger.info("Embedding provider initialized")
        return True
    except Exception as e:
        logger.error(f"Error initializing embedding provider: {e}")
        return False


def fetch_all_agents_from_letta() -> List[Dict[str, Any]]:
    """Fetch all agents from Letta API."""
    try:
        url = f"{LETTA_BASE_URL}/v1/agents"
        headers = {
            "Authorization": f"Bearer {LETTA_PASSWORD}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Fetching agents from Letta: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        agents = response.json()
        logger.info(f"Fetched {len(agents)} agents from Letta")
        return agents
        
    except Exception as e:
        logger.error(f"Error fetching agents from Letta: {e}")
        return []


def extract_agent_metadata(agent: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and format agent metadata for registry."""
    # Extract capabilities from tools
    capabilities = []
    if "tools" in agent:
        capabilities = [tool.get("name", "") for tool in agent.get("tools", [])]
    
    # Extract description from system prompt or use default
    description = agent.get("system", "")
    if not description and agent.get("name"):
        description = f"Letta agent: {agent['name']}"
    
    # Create tags from agent metadata
    tags = ["letta"]
    if agent.get("llm_config", {}).get("model"):
        tags.append(f"model:{agent['llm_config']['model']}")
    
    return {
        "agent_id": agent["id"],
        "name": agent.get("name", agent["id"]),
        "description": description[:1000],  # Limit description length
        "capabilities": capabilities[:50],  # Limit number of capabilities
        "status": "active",
        "tags": tags,
        "created_at": agent.get("created_at", datetime.now(timezone.utc).isoformat()),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


def sync_agent_to_registry(agent_data: Dict[str, Any]) -> bool:
    """Sync a single agent to the registry."""
    try:
        collection = weaviate_client.collections.get(COLLECTION_NAME)
        agent_id = agent_data["agent_id"]
        
        # Check if agent already exists
        existing = collection.query.fetch_objects(
            filters=Filter.by_property("agent_id").equal(agent_id),
            limit=1
        )
        
        # Generate embedding
        embedding_text = f"{agent_data['description']} {' '.join(agent_data['capabilities'])}"
        embedding = embedding_provider.get_embedding(embedding_text)
        
        if len(existing.objects) > 0:
            # Update existing agent
            uuid = existing.objects[0].uuid
            collection.data.update(
                uuid=uuid,
                properties=agent_data,
                vector=embedding
            )
            logger.debug(f"Updated agent: {agent_id}")
        else:
            # Insert new agent
            collection.data.insert(
                properties=agent_data,
                vector=embedding
            )
            logger.info(f"Added new agent: {agent_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error syncing agent {agent_data.get('agent_id')}: {e}")
        return False


def sync_agents():
    """Main sync function - fetch agents from Letta and update registry."""
    logger.info("="*60)
    logger.info("Starting agent sync...")
    
    start_time = time.time()
    
    # Fetch agents from Letta
    letta_agents = fetch_all_agents_from_letta()
    if not letta_agents:
        logger.warning("No agents fetched from Letta")
        return
    
    # Process and sync each agent
    success_count = 0
    error_count = 0
    
    for agent in letta_agents:
        try:
            agent_metadata = extract_agent_metadata(agent)
            if sync_agent_to_registry(agent_metadata):
                success_count += 1
            else:
                error_count += 1
        except Exception as e:
            logger.error(f"Error processing agent {agent.get('id')}: {e}")
            error_count += 1
    
    elapsed = time.time() - start_time
    logger.info(f"Sync completed in {elapsed:.2f}s: {success_count} successful, {error_count} errors")
    logger.info("="*60)


def main():
    """Main service loop."""
    logger.info("Agent Registry Sync Service starting...")
    
    # Initialize connections
    if not init_weaviate_client():
        logger.error("Failed to initialize Weaviate. Exiting.")
        sys.exit(1)
    
    if not init_embedding_provider():
        logger.error("Failed to initialize embedding provider. Exiting.")
        sys.exit(1)
    
    logger.info(f"Sync interval: {SYNC_INTERVAL} seconds")
    
    # Initial sync
    sync_agents()
    
    # Periodic sync loop
    while True:
        try:
            time.sleep(SYNC_INTERVAL)
            sync_agents()
        except KeyboardInterrupt:
            logger.info("Shutting down sync service...")
            break
        except Exception as e:
            logger.error(f"Error in sync loop: {e}")
            time.sleep(60)  # Wait before retrying


if __name__ == "__main__":
    main()
