# Letta Webhook Receiver with Graphiti Knowledge Integration

A production-ready Flask-based webhook receiver that integrates with Letta agents to provide contextual knowledge from Graphiti's semantic knowledge graph. Features automatic memory management, tool attachment, and agent tracking.

## 🎯 Current Features

**Active Integrations:**
- **🧠 Graphiti Knowledge Graph**: Semantic search across nodes and facts with deduplication
- **💾 Memory Management**: Automatic cumulative context building with smart truncation (4800 char limit)
- **🔧 Tool Auto-Attachment**: Dynamic tool discovery and attachment based on agent prompts
- **👥 Agent Tracking**: New agent detection with Matrix client notifications
- **🤝 Agent Discovery & Registry**: Semantic search for relevant agents and auto-registration (NEW!)

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
- `AGENT_REGISTRY_URL`: URL of the agent registry service (default: http://192.168.50.90:8020)

#### Context Retrieval Configuration
- `GRAPHITI_MAX_NODES`: Maximum nodes to retrieve from knowledge graph (default: 8)
- `GRAPHITI_MAX_FACTS`: Maximum facts to retrieve from knowledge graph (default: 20)
- `AGENT_REGISTRY_MAX_AGENTS`: Maximum agents to show in discovery (default: 5)
- `AGENT_REGISTRY_MIN_SCORE`: Minimum relevance score 0-1 for agents (default: 0.5)

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