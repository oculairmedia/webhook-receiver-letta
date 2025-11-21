# Letta Webhook Receiver Project

## Purpose
A Flask-based webhook receiver service that connects to Graphiti for enhanced knowledge retrieval with advanced semantic filtering and query enhancement capabilities. The service integrates with Letta agents to provide contextual information from multiple sources.

## Key Features
1. **Enhanced Knowledge Retrieval**: Uses Graphiti API for semantic context retrieval with relevance filtering
2. **BigQuery GDELT Integration**: Automatically provides global event context for news/geopolitical queries
3. **ArXiv Integration**: Retrieves academic papers for research-related queries
4. **Memory Management**: Manages Letta agent memory blocks with cumulative context building
5. **Tool Auto-Attachment**: Automatically attaches relevant tools to agents based on context
6. **Agent Tracking**: Tracks new agents and notifies Matrix client
7. **Simulation Suite**: Comprehensive testing framework for retrieval quality

## Tech Stack
- **Language**: Python 3.11
- **Web Framework**: Flask 3.0.0
- **APIs**: Letta, Graphiti, BigQuery (GDELT), ArXiv
- **ML/Semantic**: sentence-transformers, scikit-learn
- **Data Processing**: pandas, numpy
- **Visualization**: matplotlib, seaborn
- **Containerization**: Docker, Docker Compose
- **LLM Integration**: Cerebras Cloud SDK for query refinement

## Architecture
- **Main Application**: `webhook_server/app.py` - Flask webhook endpoint receiver
- **Configuration**: `webhook_server/config.py` - API URLs, credentials, configuration
- **Memory Management**: `webhook_server/memory_manager.py` - Letta memory block operations
- **Context Building**: `webhook_server/context_utils.py` - Cumulative context and deduplication
- **Integrations**: `webhook_server/integrations.py` - ArXiv and GDELT integration triggers
- **Block Finders**: `webhook_server/block_finders.py` - Finding memory blocks for agents
- **Tool Management**: `tool_manager.py` - Auto-attachment of tools to agents
- **Simulation**: `simulation_suite.py` - Testing and analysis framework

## Deployment
- Docker-based deployment with multiple Dockerfile variants
- Docker Compose configurations for local and production
- Exposes port 8290 (internal), mapped to 5005 (external)
- Health check endpoint at `/health`
