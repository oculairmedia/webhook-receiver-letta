# Codebase Structure

## Core Application (`webhook_server/`)
Main package containing the Flask webhook application.

### `webhook_server/app.py`
- Main Flask application and webhook endpoint
- Agent tracking and Matrix notifications
- Graphiti API integration for context retrieval
- Memory block creation and management
- Tool auto-attachment logic
- Entry point with argparse CLI

### `webhook_server/config.py`
- Environment variable configuration
- API URLs (Letta, Graphiti)
- Authentication headers
- Default values for retrieval parameters
- Helper functions: `get_api_url()`, `get_graphiti_config()`

### `webhook_server/memory_manager.py`
- `update_memory_block()` - Update existing blocks with cumulative context
- `attach_block_to_agent()` - Attach memory blocks to agents
- `create_memory_block()` - Create new memory blocks for agents

### `webhook_server/context_utils.py`
- `_build_cumulative_context()` - Append new context with deduplication
- `_truncate_oldest_entries()` - Manage context size limits
- `_is_content_similar_with_query_awareness()` - Similarity detection
- `_parse_context_entries()` - Parse timestamped context entries

### `webhook_server/integrations.py`
- `arxiv_integration()` - Trigger ArXiv paper retrieval
- `gdelt_integration()` - Trigger BigQuery GDELT event retrieval

### `webhook_server/block_finders.py`
- `find_memory_block()` - Locate existing memory blocks by label

## Root-Level Utilities

### `tool_manager.py`
- Tool discovery and attachment to agents
- `find_attach_tools()` - Main tool attachment logic

### `letta_tool_utils.py`
- Letta API tool utilities
- `get_find_tools_id_with_fallback()` - Get tool IDs with fallback

### `arxiv_integration.py`
- Standalone ArXiv API integration
- Paper search and metadata extraction

### `run_server.py`
- Primary entry point for running the server
- Handles imports and path configuration
- CLI argument parsing

## Testing & Simulation

### `simulation_suite.py`
- Comprehensive testing framework
- Quality metrics and analysis
- Generates reports with charts

### Test Files (`test_*.py`)
Over 40 test files for various components:
- Integration tests (ArXiv, GDELT, Graphiti, Letta)
- Webhook flow tests
- Memory block operation tests
- API connection tests
- Fix verification tests

### Debug Scripts
- `debug_*.py` - Debug specific components
- `verify_*.py` - Verification scripts
- `check_*.py` - Quick check utilities

## Configuration Files

### Docker
- `Dockerfile` - Production image
- `Dockerfile.light` - Lightweight variant
- `Dockerfile.production` - Production-optimized
- `Dockerfile.debug` - Debug variant
- `compose.yaml`, `compose-prod.yaml`, `docker-compose-local.yml` - Docker Compose configs

### Dependencies
- `requirements.txt` - Full Python dependencies
- `requirements-light.txt` - Minimal dependencies

### Other
- `.gitignore` - Git ignore patterns
- `.dockerignore` - Docker build exclusions
- `run-webhook-service.sh/.bat` - Convenience scripts

## Output Directories

### `large_simulation_output/`
- Results from large-scale simulations
- JSON results, charts, reports

### `test_simulation_output/`
- Results from test simulations
- Smaller scale testing outputs

## Documentation

### Markdown Files
- `README.md` - Main project documentation
- `README_*.md` - Feature-specific documentation
- `*_SUMMARY.md` - Fix and implementation summaries
- `TROUBLESHOOTING.md` - Common issues and solutions

## Hidden Directories
- `.claude/` - Claude Code configuration
- `.letta/` - Letta-specific settings
- `.serena/` - Serena agent configuration
