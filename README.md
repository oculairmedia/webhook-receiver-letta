# Letta Webhook Receiver with Graphiti Knowledge Integration

A production-ready Flask-based webhook receiver that integrates with Letta agents to provide contextual knowledge from Graphiti's semantic knowledge graph. Features automatic memory management, tool attachment, and agent tracking.

## 🎯 Current Features

**Active Integrations:**
- **🧠 Graphiti Knowledge Graph**: Semantic search across nodes and facts with deduplication
- **💾 Memory Management**: Automatic cumulative context building with smart truncation (4800 char limit)
- **🔧 Tool Auto-Attachment**: Dynamic tool discovery and attachment based on agent prompts
- **👥 Agent Tracking**: New agent detection with Matrix client notifications
- **🤝 Agent Discovery & Registry**: Semantic search for relevant agents with auto-sync (NEW!)
- **🔌 MCP Server**: FastMCP HTTP server exposing `find_agents` tool for agent collaboration (NEW!)

**Note**: ArXiv and GDELT integrations are currently disabled but remain in codebase for future reactivation.

## 🔥 Request Hotpath & Architecture

### Overview
The webhook service processes incoming Letta agent requests through a multi-stage pipeline that retrieves context from Graphiti, manages memory blocks, and attaches relevant tools.

### Request Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. WEBHOOK RECEIPT                           │
│  POST /webhook or /webhook/letta                                │
│  • Extract agent_id and prompt from webhook payload             │
│  • Support for message_sent and stream_started events           │
│  • Track new agents for Matrix notifications                    │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              2. CONTEXT GENERATION (Graphiti)                   │
│  generate_context_from_prompt(prompt, agent_id)                 │
│  • Query Graphiti API for semantic nodes & facts                │
│  • Deduplicate facts by text content                            │
│  • Format context with node summaries and facts                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              3. MEMORY BLOCK MANAGEMENT                         │
│  create_memory_block(block_data, agent_id)                      │
│  • Find or create "graphiti_context" block                      │
│  • Build cumulative context with timestamps                     │
│  • Deduplicate similar entries                                  │
│  • Truncate oldest entries if > 4800 chars                      │
│  • Auto-attach block to agent if needed                         │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              4. AGENT DISCOVERY (NEW!)                          │
│  query_agent_registry(query, limit, min_score)                  │
│  • Semantic search for relevant agents                          │
│  • Create/update "available_agents" memory block                │
│  • Show top 5 agents with capabilities & status                 │
│  • Non-blocking: continues on failure                           │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              5. TOOL AUTO-ATTACHMENT                            │
│  find_attach_tools(query, agent_id)                             │
│  • Search for relevant tools based on prompt                    │
│  • Preserve existing tools + find_tools utility                 │
│  • Attach up to 3 new tools (min_score: 70.0)                   │
│  • Non-blocking: continues on failure                           │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
              ┌──────────────┐
              │   RESPONSE   │
              │  200 OK      │
              └──────────────┘
```

### Performance Characteristics

**Typical Request Time**: 1-3 seconds
- Graphiti queries: ~500ms-1s (nodes + facts)
- Memory block operations: ~200-500ms
- Agent discovery: ~300-800ms (semantic search)
- Tool attachment: ~500ms-1s
- Total: ~1.5-3.3s (sequential)

**External Dependencies**:
| Service | Port | Purpose | Timeout |
|---------|------|---------|---------|
| Graphiti API | 8003/8001 | Knowledge graph search | 30s |
| Letta API | 8283 | Memory blocks & agents | Default |
| Tool Attachment | 8020 | Tool discovery & attachment | 15s |
| Matrix Client | 8004 | New agent notifications | 5s |
| Agent Registry | 8021 | Semantic agent search | 15s |
| Agent Registry MCP | 8022 | MCP server with find_agents tool | N/A |
| Weaviate | 8092 | Vector database for agent registry | 30s |

### Key Implementation Details

**Memory Block Management**:
- Max context length: 4800 chars (under Letta's 5000 char limit)
- Timestamp-based deduplication
- Preserves most recent entries when truncating
- Auto-attaches blocks to agents

**Graphiti Integration**:
- Parallel queries for nodes and facts
- Retry strategy: 3 attempts with backoff
- Fact deduplication by text content
- Default limits: 8 nodes, 20 facts (configurable)

**Tool Attachment**:
- Non-blocking (webhook continues on failure)
- Preserves existing tools via "*" wildcard
- Min relevance score: 70.0
- Limit: 3 new tools per request

For detailed component documentation, see **Technical Deep Dive** section below.

## Running with Docker Compose

### Using the pre-built image from Docker Hub

1. Create a `.env.prod` file with your configuration (or use the provided template)
2. Run the service using Docker Compose:

```bash
# Start the service
docker compose -f compose-prod.yaml --env-file .env.prod up -d

# View logs
docker compose -f compose-prod.yaml logs -f

# Stop the service
docker compose -f compose-prod.yaml down
```

### Using the convenience scripts

For Windows:
```
run-webhook-service.bat
```

For Linux/macOS:
```bash
chmod +x run-webhook-service.sh
./run-webhook-service.sh
```

### Environment Variables

The following environment variables can be configured:

#### Core API Configuration
- `GRAPHITI_URL`: URL of the Graphiti API (default: http://192.168.50.90:8003)
- `LETTA_BASE_URL`: Base URL for the Letta API (default: https://letta2.oculair.ca)
- `LETTA_PASSWORD`: Password for Letta API authentication (default: lettaSecurePass123)
- `MATRIX_CLIENT_URL`: Matrix client for agent notifications (default: http://192.168.50.90:8004)
- `AGENT_REGISTRY_URL`: URL of the agent registry service (default: http://192.168.50.90:8021)

#### Context Retrieval Configuration
- `GRAPHITI_MAX_NODES`: Maximum nodes to retrieve from knowledge graph (default: 8)
- `GRAPHITI_MAX_FACTS`: Maximum facts to retrieve from knowledge graph (default: 20)
- `AGENT_REGISTRY_MAX_AGENTS`: Maximum agents to show in discovery (default: 10)
- `AGENT_REGISTRY_MIN_SCORE`: Minimum relevance score 0-1 for agents (default: 0.3)

#### Agent Registry Configuration
- `WEAVIATE_URL`: Weaviate vector database URL (default: http://weaviate:8080)
- `OLLAMA_BASE_URL`: Ollama API for embeddings (default: http://192.168.50.80:11434)
- `OLLAMA_EMBEDDING_MODEL`: Embedding model (default: dengcao/Qwen3-Embedding-4B:Q4_K_M)
- `EMBEDDING_DIMENSION`: Embedding dimensions (default: 2560)
- `AGENT_SYNC_INTERVAL`: Auto-sync interval in seconds (default: 300)

### Configuration Examples

#### Default Setup (Recommended)
```bash
GRAPHITI_URL=http://192.168.50.90:8003
GRAPHITI_MAX_NODES=8
GRAPHITI_MAX_FACTS=20
LETTA_BASE_URL=https://letta2.oculair.ca
MATRIX_CLIENT_URL=http://192.168.50.90:8004
```

#### High-Context Setup
```bash
GRAPHITI_MAX_NODES=15
GRAPHITI_MAX_FACTS=30
```

#### Minimal Setup (Faster)
```bash
GRAPHITI_MAX_NODES=3
GRAPHITI_MAX_FACTS=10
```

## Building the image locally

If you want to build the image locally instead of using the pre-built one:

```bash
# Build the image
docker build -t oculair/letta-webhook-receiver:latest .

# Run using the local compose file
docker compose up -d
```

## API Endpoints

### Webhook Endpoints
- `POST /webhook` - Primary webhook endpoint
- `POST /webhook/letta` - Letta-specific webhook endpoint (same functionality)

### Health & Monitoring
- `GET /health` - Health check with service status and timestamp
- `GET /agent-tracker/status` - View tracked agents and count
- `POST /agent-tracker/reset` - Reset agent tracking (for testing)

## 🤖 Agent Registry MCP Server

The Agent Registry MCP Server provides a Model Context Protocol (MCP) interface for agent discovery and collaboration. It exposes the `find_agents` tool that allows agents to search for other agents based on natural language queries.

### Architecture

```
┌──────────────────────────────────────────────┐
│   Agent Registry Services                    │
├──────────────────────────────────────────────┤
│                                              │
│  ┌────────────────┐    ┌─────────────────┐  │
│  │ Agent Registry │    │ FastMCP Server  │  │
│  │ API (8021)     │    │ (8022/mcp)      │  │
│  │                │    │                 │  │
│  │ - Search       │    │ - find_agents   │  │
│  │ - Register     │    │ - HTTP/MCP      │  │
│  └────────┬───────┘    └─────────────────┘  │
│           │                                  │
│           ▼                                  │
│  ┌────────────────────┐                     │
│  │ Weaviate (8092)    │                     │
│  │ - Vector storage   │                     │
│  │ - Semantic search  │                     │
│  └────────┬───────────┘                     │
│           │                                  │
│           ▼                                  │
│  ┌────────────────────┐                     │
│  │ Sync Service       │                     │
│  │ - Fetch from Letta │                     │
│  │ - Every 5 minutes  │                     │
│  └────────────────────┘                     │
└──────────────────────────────────────────────┘
```

### MCP Server Details

**Endpoint**: `http://192.168.50.90:8022/mcp`  
**Transport**: HTTP (Streamable HTTP protocol)  
**Framework**: FastMCP 2.13+

#### Available Tools

##### `find_agents`
Search for relevant agents in the agent registry based on natural language queries.

**Parameters:**
- `query` (string, required): Search query describing what kind of agent you're looking for
  - Examples: "machine learning expert", "database administrator", "content writer"
- `limit` (integer, optional): Maximum number of agents to return (default: 10, max: 50)
- `min_score` (float, optional): Minimum relevance score 0.0-1.0 (default: 0.3)

**Returns:**
Formatted string with:
- Agent IDs
- Names and descriptions
- Capabilities
- Relevance scores
- Status (active/inactive)
- Tip to use `matrix_agent_message` tool for messaging

**Example Usage:**
```python
# From an agent with MCP access
result = find_agents(
    query="python developer with API experience",
    limit=5,
    min_score=0.4
)
```

**Example Output:**
```
Found 3 relevant agents:

1. **Python API Expert** (ID: `agent-abc123`)
   Status: active
   Relevance: 0.87
   Description: Specialized in building RESTful APIs with Python and FastAPI...
   Capabilities: api-development, python, fastapi

2. **Backend Developer** (ID: `agent-def456`)
   Status: active
   Relevance: 0.72
   Description: Full-stack developer focusing on backend services...
   Capabilities: python, flask, databases

💡 Tip: You can message these agents using the matrix_agent_message tool with their agent ID.
```

#### Available Resources

##### `agent-registry://stats`
Get statistics about the agent registry including total agents, embeddings, and sync status.

### Registration with Claude Code

To register the MCP server with Claude Code:

```bash
claude mcp add --transport http agent-registry http://192.168.50.90:8022/mcp -s user
```

This makes the `find_agents` tool available to all your Claude Code sessions.

### Agent Registry Services

#### 1. Agent Registry API (Port 8021)

RESTful API for agent management and search.

**Endpoints:**
- `GET /health` - Health check
- `GET /api/v1/agents/search` - Search agents
  - Query params: `query`, `limit`, `min_score`
- `POST /api/v1/agents` - Register new agent
- `GET /api/v1/stats` - Get registry statistics

#### 2. Auto-Sync Service

Background service that automatically syncs agents from Letta API to the registry.

**Configuration:**
- Sync interval: 300 seconds (5 minutes) - configurable via `AGENT_SYNC_INTERVAL`
- Fetches all agents from Letta API
- Generates embeddings using Ollama Qwen3-Embedding-4B:Q4_K_M
- Updates Weaviate vector database

**Current Status:**
- Successfully synced 50+ agents from production Letta instance
- Embedding dimensions: 2560
- Ollama endpoint: `http://192.168.50.80:11434`

#### 3. Weaviate Vector Database (Port 8092)

Stores agent embeddings for semantic search.

**Access:**
- HTTP: `http://192.168.50.90:8092`
- gRPC: `192.168.50.90:50052`

### Webhook Integration

The webhook receiver automatically queries the agent registry on each webhook and creates an `available_agents` memory block with the top 10 most relevant agents.

**Configuration:**
```bash
AGENT_REGISTRY_URL=http://192.168.50.90:8021
AGENT_REGISTRY_MAX_AGENTS=10
AGENT_REGISTRY_MIN_SCORE=0.3
```

### Container Health Status

All agent registry services are monitored for health:

| Service | Port | Health Status |
|---------|------|---------------|
| agent-registry-weaviate | 8092 | ✅ Monitored |
| agent-registry-service | 8021 | ✅ Monitored |
| agent-registry-sync | - | Background worker |
| agent-registry-mcp | 8022 | MCP server |

## Troubleshooting

### Common Issues

**Connection Issues with Graphiti:**
1. Ensure Graphiti API is running and accessible
2. Check network settings in Docker Compose file
3. Verify `GRAPHITI_URL` environment variable
4. Test with: `curl http://192.168.50.90:8003/health`

**Memory Block Issues:**
1. Check Letta API is accessible
2. Verify `LETTA_PASSWORD` is correct
3. Check logs for `[attach_block_to_agent]` errors
4. Ensure agent_id format is correct (`agent-xxx`)

**Tool Attachment Failures:**
1. Non-blocking - webhook will continue
2. Check port 8020 tool service is running
3. Review `[AUTO_TOOL_ATTACHMENT]` logs
4. Verify `min_score` threshold isn't too high

**Agent Registry Issues:**
1. Check Weaviate is healthy: `docker ps | grep weaviate`
2. Verify agent registry service: `curl http://192.168.50.90:8021/health`
3. Test MCP endpoint: `curl http://192.168.50.90:8022/mcp`
4. Check sync service logs: `docker logs agent-registry-sync`
5. Verify Ollama is accessible: `curl http://192.168.50.80:11434/api/tags`

**MCP Server Not Accessible:**
1. Ensure FastMCP CLI is installed in container
2. Check port mapping: 8022 (host) → 8000 (container)
3. Review MCP server logs: `docker logs agent-registry-mcp`
4. Verify HTTP transport is enabled (not SSE)
5. Test with: `curl -H "Accept: text/event-stream" http://192.168.50.90:8022/mcp`

### Log Prefixes for Debugging
- `[WEBHOOK_DEBUG]` - Request/response details
- `[GRAPHITI]` - Graphiti API operations
- `[AGENT_TRACKER]` - Agent tracking/notifications
- `[AGENT_REGISTRY]` - Agent registration and discovery
- `[AGENT_DISCOVERY]` - Agent search operations
- `[AUTO_TOOL_ATTACHMENT]` - Tool attachment operations
- `[attach_block_to_agent]` - Memory block operations
- `[_build_cumulative_context]` - Context building logic

## Docker Hub Repository

The Docker image is available at: [oculair/letta-webhook-receiver](https://hub.docker.com/r/oculair/letta-webhook-receiver)

---

## 📚 Technical Deep Dive

### Component Details

#### 1. Webhook Receipt (webhook_server/app.py:233-297)
**Entry Points**: `/webhook`, `/webhook/letta`

**Processing Flow**:
```python
# Extract agent_id from response or request path
if data.get("response"):
    agent_id = data["response"].get("agent_id")
elif "/agents/" in path:
    # Parse from path: /v1/agents/agent-xxx/messages
    path_parts = path.split("/")
    agent_id = path_parts[path_parts.index("agents") + 1]

# Handle list-format prompts
if isinstance(prompt, list):
    prompt_text = " ".join([item.get("text", "") for item in prompt if item.get("type") == "text"])
```

**Agent Tracking**:
- Thread-safe tracking with `threading.Lock()`
- Background Matrix notification (non-blocking)
- 5-second timeout for notifications

#### 2. Graphiti Context Generation (webhook_server/app.py:96-224)

**Two-Phase Search**:
```python
# Phase 1: Node Search
POST {GRAPHITI_URL}/search/nodes
{
  "query": "user prompt",
  "max_nodes": 8,
  "group_ids": []  # Empty = all groups
}

# Phase 2: Fact Search  
POST {GRAPHITI_URL}/search
{
  "query": "user prompt",
  "max_facts": 20,
  "group_ids": []
}
```

**Response Processing**:
- Deduplicates facts by exact text match
- Formats as: `Node: {name}\nSummary: {summary}\n\nFact: {fact}`
- Prefixes with "Relevant Entities from Knowledge Graph:"
- Falls back to error message on timeout/failure

**Retry Configuration**:
- Total retries: 3
- Backoff factor: 1 (1s, 2s, 4s delays)
- Retry on: 429, 500, 502, 503, 504 status codes
- Timeout: 30 seconds per request

#### 3. Memory Block Management (webhook_server/memory_manager.py)

**Block Lifecycle**:
```python
def create_memory_block(block_data, agent_id):
    # 1. Find existing block by label
    block, is_attached = find_memory_block(agent_id, "graphiti_context")
    
    # 2. Auto-attach if exists but not attached
    if block and not is_attached:
        attach_block_to_agent(agent_id, block['id'])
    
    # 3. Update with cumulative context
    if block:
        return update_memory_block(block['id'], block_data, agent_id, block)
    
    # 4. Create new block + auto-attach
    new_block = requests.post(f"{LETTA_BASE_URL}/v1/blocks", json=block_data)
    attach_block_to_agent(agent_id, new_block['id'])
    return new_block
```

**Cumulative Context Building** (webhook_server/context_utils.py):
```python
def _build_cumulative_context(existing, new):
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    separator = f"\n\n--- CONTEXT ENTRY ({timestamp}) ---\n\n"
    
    # Deduplication check
    if _is_content_similar_with_query_awareness(most_recent, new):
        return existing  # Skip duplicate
    
    cumulative = existing + separator + new
    
    # Truncate if > 4800 chars
    if len(cumulative) > 4800:
        cumulative = _truncate_oldest_entries(cumulative, 4800)
    
    return cumulative
```

**Truncation Strategy**:
1. Parse entries by timestamp separators
2. Always preserve most recent entry
3. Work backwards to fit older entries
4. Add "--- OLDER ENTRIES TRUNCATED ---" marker
5. If newest entry alone > limit, truncate it with "[CONTENT TRUNCATED]"

**Deduplication**:
- 90% character overlap threshold
- Query-aware for ArXiv searches (different queries = different content)
- Timestamp-aware for Graphiti (different timestamps = different searches)

#### 4. Tool Auto-Attachment (tool_manager.py)

**External API Call**:
```python
POST http://192.168.50.90:8020/api/v1/tools/attach
{
  "query": "user prompt",
  "agent_id": "agent-xxx",
  "keep_tools": ["*", "find_tools_id"],  # Preserve all + utility
  "limit": 3,
  "min_score": 70.0,
  "request_heartbeat": false
}
```

**Keep Tools Logic**:
- `"*"` = wildcard to preserve all existing tools
- Dynamically looks up `find_tools` utility ID
- Combines: `["*", find_tools_id]`

**Error Handling**:
```python
try:
    tool_result = find_attach_tools(...)
except Exception as e:
    print(f"[AUTO_TOOL_ATTACHMENT] Error: {e}")
    # Continue - don't fail webhook
```

**Response Parsing**:
- `successful_attachments`: New tools added
- `detached_tools`: Tools removed
- `preserved_tools`: Tools kept (confirmed by API)

### File Structure

```
webhook_server/
  ├── app.py              - Main Flask app & webhook endpoint
  ├── config.py           - Environment config & API URLs
  ├── memory_manager.py   - Block create/update/attach logic
  ├── context_utils.py    - Cumulative context & truncation
  ├── block_finders.py    - Find existing blocks by label
  └── integrations.py     - ArXiv/GDELT stubs (disabled)

tool_manager.py           - Tool attachment API client
letta_tool_utils.py       - Letta tool utility functions
arxiv_integration.py      - ArXiv integration (not used)
run_server.py             - Entry point with CLI args
```

### Database/State

**No Persistent Storage**: All state managed via external APIs:
- Agent memory: Letta API (memory blocks)
- Knowledge graph: Graphiti API
- Tool registry: Tool Attachment API (port 8020)
- Agent tracking: In-memory set (lost on restart)

### Security Considerations

**Authentication**:
- Letta API: `X-BARE-PASSWORD` header + `Bearer` token
- User isolation: `user_id` header set to `agent_id`
- No webhook authentication (internal service)

**Resource Limits**:
- Context max: 4800 chars (prevents Letta API errors)
- Tool limit: 3 new tools per request
- Graphiti limits: Configurable nodes/facts
- Timeouts: 5s-30s depending on service

### Monitoring Recommendations

**Key Metrics**:
1. Webhook response time (target: < 3s)
2. Graphiti API success rate (target: > 95%)
3. Memory block attachment failures
4. Context truncation frequency
5. Agent growth rate

**Alert Thresholds**:
- Response time > 5s
- Graphiti timeout rate > 10%
- Memory block errors > 5%
- Context truncation > 80% of requests
## 🧪 Testing

### Test Infrastructure

This project uses `pytest` with comprehensive test coverage including unit tests, integration tests, and end-to-end tests.

**Current Test Coverage**: Target 80%+ overall, 90%+ for critical modules

### Running Tests

#### Run All Tests
```bash
pytest
```

#### Run Unit Tests Only
```bash
pytest tests/unit/ -v
```

#### Run Integration Tests
```bash
pytest tests/integration/ -v
```

#### Run E2E Tests
```bash
pytest tests/e2e/ -v
```

#### Run with Coverage Report
```bash
pytest --cov=webhook_server --cov=tool_manager --cov=letta_tool_utils --cov-report=html
```

View the coverage report: `open htmlcov/index.html`

#### Run Specific Test File
```bash
pytest tests/unit/test_context_utils.py -v
```

#### Run Tests Matching Pattern
```bash
pytest -k "test_graphiti" -v
```

### Test Categories

#### Unit Tests (`tests/unit/`)
Test individual functions and classes in isolation:
- `test_config.py` - Configuration loading and validation
- `test_context_utils.py` - Context building, deduplication, truncation
- `test_memory_manager.py` - Memory block operations
- `test_block_finders.py` - Block finding logic
- `test_tool_manager.py` - Tool attachment functionality
- `test_app.py` - Flask endpoints and agent tracking

#### Integration Tests (`tests/integration/`)
Test interactions with external services (mocked):
- `test_graphiti.py` - Graphiti API connectivity and error handling
- `test_letta_api.py` - Letta memory block operations
- `test_tool_service.py` - Tool discovery and attachment API
- `test_matrix_client.py` - Matrix notification service

#### E2E Tests (`tests/e2e/`)
Test complete workflows from end to end:
- `test_webhook_flow.py` - Complete webhook processing pipeline
- Performance benchmarks (target: < 3s per webhook)

### Test Quality Standards

- **Isolation**: Tests don't depend on each other
- **Repeatability**: Same results on every run
- **Coverage**: Minimum 70%, target 80%
- **Speed**: Unit tests < 100ms, integration tests < 1s
- **Clarity**: Descriptive names and docstrings

### Continuous Integration

Tests run automatically on:
- Every push to `main`, `develop`, or `claude/*` branches
- Every pull request
- Python versions: 3.11, 3.12

CI pipeline includes:
1. Unit and integration tests
2. Coverage reporting
3. Code linting (flake8)
4. Security scanning (bandit, safety)

View CI status in GitHub Actions.

### Contributing Tests

When adding new features:
1. Write tests first (TDD approach recommended)
2. Ensure all tests pass: `pytest`
3. Check coverage: `pytest --cov`
4. Verify coverage doesn't decrease
5. Follow testing guidelines in [CONTRIBUTING.md](CONTRIBUTING.md)

### Common Test Patterns

#### Testing with Mocks
```python
from unittest.mock import patch, Mock

@patch('webhook_server.app.query_graphiti_api')
def test_webhook_with_graphiti(mock_graphiti, client):
    mock_graphiti.return_value = {"success": True, "context": "Test"}
    response = client.post('/webhook', json={"agent_id": "test"})
    assert response.status_code == 200
```

#### Testing API Calls
```python
import responses

@responses.activate
def test_graphiti_api_call():
    responses.add(
        responses.POST,
        "http://graphiti.example.com/search",
        json={"nodes": []},
        status=200
    )
    result = query_graphiti_api("test")
    assert result['success'] is True
```

### Debugging Tests

#### Run with Verbose Output
```bash
pytest -vv
```

#### Show Print Statements
```bash
pytest -s
```

#### Stop on First Failure
```bash
pytest -x
```

#### Run Last Failed Tests
```bash
pytest --lf
```

#### Debug with PDB
```bash
pytest --pdb
```

For more details, see [CONTRIBUTING.md](CONTRIBUTING.md) and [TESTING_PLAN.md](TESTING_PLAN.md).
