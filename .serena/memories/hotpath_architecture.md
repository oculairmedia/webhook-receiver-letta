# Webhook Service Hotpath Architecture

## Request Flow Pipeline

### 1. Webhook Receipt → 2. Context Generation → 3. Memory Management → 4. Tool Attachment

**Total Time**: 1-3 seconds typical

## Component Breakdown

### 1. Webhook Receipt (app.py:233-297)
**Endpoints**: POST /webhook, POST /webhook/letta

**Extraction Logic**:
- agent_id: From response.agent_id or extracted from path /v1/agents/{agent_id}/messages
- prompt: Direct or from list of {"type": "text", "text": "..."} objects
- event_type: message_sent or stream_started

**Agent Tracking**:
- Thread-safe set of known agents (in-memory)
- Background Matrix notification on new agent detection
- Non-blocking (5s timeout)

### 2. Context Generation (app.py:96-224)
**Function**: generate_context_from_prompt() → query_graphiti_api()

**Graphiti API Calls** (parallel):
- POST {GRAPHITI_URL}/search/nodes → max 8 nodes (default)
- POST {GRAPHITI_URL}/search → max 20 facts (default)
- Retry: 3 attempts with backoff (1s, 2s, 4s)
- Timeout: 30s per request

**Processing**:
- Deduplicate facts by text content
- Format: "Relevant Entities from Knowledge Graph:\nNode: {name}\nSummary: {summary}\n\nFact: {fact}"
- On error: Returns error message but continues webhook

**ArXiv Integration**: Currently disabled (integrations.py:4-14) - dummy class

### 3. Memory Block Management (memory_manager.py)
**Function**: create_memory_block() → _build_cumulative_context()

**Block Operations**:
1. find_memory_block(agent_id, "graphiti_context")
2. If exists but not attached → attach_block_to_agent()
3. Build cumulative context with timestamp separators
4. Update existing or create new block
5. Auto-attach new blocks to agent

**Cumulative Context** (context_utils.py:9-57):
- Max length: 4800 chars (under Letta's 5000 limit)
- Timestamp format: "--- CONTEXT ENTRY (YYYY-MM-DD HH:MM:SS UTC) ---"
- Deduplication: 90% character overlap threshold, query-aware
- Truncation: Preserves newest entry, works backwards for older entries
- Marker: "--- OLDER ENTRIES TRUNCATED ---"

**Key Fix**: Always includes new content even after truncation

### 4. Tool Auto-Attachment (tool_manager.py:72-170)
**External Service**: POST http://192.168.50.90:8020/api/v1/tools/attach

**Parameters**:
- query: User prompt
- agent_id: Current agent
- keep_tools: ["*", find_tools_id] - preserves all existing + utility
- limit: 3 new tools max
- min_score: 70.0 relevance threshold
- request_heartbeat: false

**Error Handling**: Non-blocking - logs error and continues webhook

## API Endpoints

### Webhook
- POST /webhook or /webhook/letta - Main webhook endpoint

### Monitoring
- GET /health - Service health check
- GET /agent-tracker/status - View tracked agents
- POST /agent-tracker/reset - Clear agent tracking (testing)

## External Dependencies

| Service | Port | Purpose | Timeout |
|---------|------|---------|---------|
| Graphiti | 8003 | Knowledge graph | 30s |
| Letta | 8283 | Memory & agents | Default |
| Tool Attach | 8020 | Tool discovery | 15s |
| Matrix | 8004 | Agent notifications | 5s |

## Configuration

**Environment Variables**:
- GRAPHITI_URL (default: http://192.168.50.90:8003)
- GRAPHITI_MAX_NODES (default: 8)
- GRAPHITI_MAX_FACTS (default: 20)
- LETTA_BASE_URL (default: https://letta2.oculair.ca)
- LETTA_PASSWORD (default: lettaSecurePass123)
- MATRIX_CLIENT_URL (default: http://192.168.50.90:8004)

## Log Prefixes

- [WEBHOOK_DEBUG] - Request/response details
- [GRAPHITI] - Graphiti operations
- [AGENT_TRACKER] - Agent tracking
- [AUTO_TOOL_ATTACHMENT] - Tool attachment
- [attach_block_to_agent] - Memory blocks
- [_build_cumulative_context] - Context building

## Performance Notes

**Bottlenecks**:
1. Graphiti API calls (~500ms-1s)
2. Memory block operations (~200-500ms)
3. Tool attachment (~500ms-1s)

**Optimization Opportunities**:
- Graphiti calls could be parallelized (currently sequential)
- Memory block caching could reduce API calls
- Tool attachment could be truly async

**Failure Modes**:
- Graphiti timeout → Error context returned, webhook continues
- Memory block error → Webhook fails with 500
- Tool attachment error → Logged, webhook continues
- Matrix notification error → Logged, webhook continues
