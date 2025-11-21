# Agent Registry Service

A Flask-based service for registering and discovering Letta agents using semantic search with Weaviate vector database.

## Features

- **Agent Registration**: Auto-register agents with capabilities and metadata
- **Semantic Search**: Find relevant agents based on natural language queries
- **Vector Embeddings**: Uses sentence-transformers for semantic matching
- **Status Management**: Track agent online/offline status
- **RESTful API**: Clean REST endpoints for all operations

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Start both Weaviate and Agent Registry service
docker-compose up -d

# View logs
docker-compose logs -f agent-registry

# Stop services
docker-compose down
```

### Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export WEAVIATE_URL="http://localhost:8080"
export EMBEDDING_MODEL="all-MiniLM-L6-v2"
export PORT=8020

# Run the service
python app.py
```

## API Endpoints

### Health Check
```bash
GET /health
```

### Register Agent
```bash
POST /api/v1/agents/register
Content-Type: application/json

{
  "agent_id": "agent-xxx",
  "name": "Agent Name",
  "description": "Agent description and capabilities",
  "capabilities": ["capability1", "capability2"],
  "status": "active",
  "tags": ["tag1"],
  "created_at": "2025-11-21T12:00:00Z",
  "updated_at": "2025-11-21T12:00:00Z"
}
```

### Search Agents
```bash
GET /api/v1/agents/search?query=database+optimization&limit=5&min_score=0.5
```

Response:
```json
{
  "success": true,
  "agents": [
    {
      "agent_id": "agent-xxx",
      "name": "Database Expert",
      "description": "Specializes in database optimization",
      "capabilities": ["SQL", "performance tuning"],
      "status": "active",
      "score": 0.85
    }
  ],
  "count": 1,
  "query": "database optimization"
}
```

### Get Agent Details
```bash
GET /api/v1/agents/{agent_id}
```

### Update Agent Status
```bash
PUT /api/v1/agents/{agent_id}/status
Content-Type: application/json

{
  "status": "offline"
}
```

### Delete Agent
```bash
DELETE /api/v1/agents/{agent_id}
```

## Configuration

Environment variables:

- `WEAVIATE_URL` - Weaviate instance URL (default: http://192.168.50.90:8080)
- `EMBEDDING_MODEL` - Sentence-transformers model (default: all-MiniLM-L6-v2)
- `PORT` - Service port (default: 8020)

## Architecture

```
Agent Registry Service (:8020)
    ↓
Weaviate Vector DB (:8080)
    ↓
Semantic Search with Embeddings
    ↓
Agent Discovery Results
```

## Integration with Webhook Receiver

The webhook receiver automatically:
1. Detects new agents
2. Registers them with this service
3. Queries for relevant agents on each message
4. Injects "available_agents" into memory blocks

## Development

### Running Tests
```bash
pytest tests/
```

### Building Docker Image
```bash
docker build -t agent-registry:latest .
```

## Troubleshooting

**Connection Issues:**
- Check Weaviate is running: `curl http://localhost:8080/v1/meta`
- Verify network connectivity
- Check Docker logs: `docker-compose logs weaviate`

**Slow First Request:**
- First request downloads embedding model (~80MB)
- Subsequent requests are fast (model cached)

**Search Returns No Results:**
- Lower `min_score` parameter (default: 0.5)
- Check agents are registered: `GET /api/v1/agents/search?query=*&limit=100`
- Verify embedding model loaded: `GET /health`

## Performance

- **Registration**: ~200-500ms (includes embedding generation)
- **Search**: ~100-300ms (cached embeddings)
- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions, fast inference)
- **Concurrent Requests**: Supports 50+ concurrent searches

## License

Part of the Letta Webhook Receiver project.
