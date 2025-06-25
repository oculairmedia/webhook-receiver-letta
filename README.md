# Letta Webhook Receiver with Enhanced Knowledge Retrieval

A Flask-based webhook receiver that connects to Graphiti for retrieving context with advanced semantic filtering and query enhancement capabilities.

## 🎯 Enhanced Retrieval Features

This webhook service includes production-ready improved retrieval strategies that significantly enhance the relevance of retrieved context:

- **🧠 Semantic Relevance Filtering**: Uses sentence transformers to calculate actual semantic similarity between queries and retrieved content
- **🔍 Query Enhancement**: Automatically generates domain-specific query variants for better coverage (e.g., "AI" → "artificial intelligence machine learning")
- **⚡ Dynamic Result Optimization**: Returns fewer but higher-quality results with adaptive relevance thresholds
- **🔄 Graceful Fallbacks**: Works even when semantic libraries are unavailable, falling back to keyword matching
- **📊 Quality Metrics**: Provides relevance scores and debugging information for transparency
- **🎯 Bias Correction**: Specifically designed to improve retrieval relevance even with biased or system-focused knowledge graphs

### Performance Improvements

**Before Enhancement**: Generic system entities about webhooks/infrastructure
**After Enhancement**:
- Python queries: 0.795 avg relevance with actual Python code/implementation content
- AI queries: 0.573 avg relevance with real AI integration and agentic systems
- Domain queries: 0.538+ avg relevance with contextually relevant technical content

## 🗃️ BigQuery GDELT Integration

This service now includes intelligent BigQuery GDELT (Global Database of Events, Language, and Tone) integration that automatically provides global event context when relevant:

- **🌍 Smart Event Detection**: Automatically detects queries about global events, news, politics, and geopolitical topics
- **📊 Rich Data Retrieval**: Pulls detailed event data from GDELT's comprehensive database including actors, locations, sentiment, and sources
- **🧠 Dual Memory System**: Creates separate "bigquery" memory blocks alongside "graphiti_context" blocks for structured vs. semantic data
- **⚡ Contextual Triggering**: Only invokes BigQuery when the Cerebras model determines it would be valuable
- **🔧 Configurable Queries**: Uses verbose GDELT queries by default but supports custom query types

### BigQuery Features

- **Event Analysis**: Recent global events with detailed actor, location, and sentiment data
- **Source Attribution**: Includes URLs and source information for fact-checking
- **Geographic Context**: Full location names and country codes for spatial understanding
- **Temporal Tracking**: Timestamps and date information for chronological context
- **Tone Analysis**: Sentiment scores from -100 (very negative) to +100 (very positive)

### Triggering Keywords

BigQuery is automatically invoked for queries containing terms like:
- Global events: "news", "events", "world", "international", "politics"
- Geographic: country names, regions, "diplomatic", "foreign policy"
- Event types: "conflict", "protest", "cooperation", "crisis", "sanctions"
- Direct requests: "gdelt", "bigquery", "recent events"

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
- `GRAPHITI_URL`: URL of the Graphiti API (default: http://192.168.50.90:8001/api)
- `LETTA_BASE_URL`: Base URL for the Letta API (default: https://letta2.oculair.ca)
- `LETTA_PASSWORD`: Password for Letta API authentication (default: lettaSecurePass123)
- `CEREBRAS_API_KEY`: API key for Cerebras query refinement service

#### Context Retrieval Configuration
- `GRAPHITI_MAX_NODES`: Maximum number of nodes to retrieve from knowledge graph (default: 2)
- `GRAPHITI_MAX_FACTS`: Maximum number of facts to retrieve from knowledge graph (default: 10)
- `GRAPHITI_WEIGHT_LAST_MESSAGE`: Weight for the last message in context retrieval (default: 0.6)
- `GRAPHITI_WEIGHT_PREVIOUS_ASSISTANT_MESSAGE`: Weight for the previous assistant message (default: 0.25)
- `GRAPHITI_WEIGHT_PRIOR_USER_MESSAGE`: Weight for the prior user message (default: 0.15)

#### Enhanced Retrieval Configuration
- `RETRIEVAL_RELEVANCE_THRESHOLD`: Minimum semantic similarity score to include results (default: 0.25)
- `RETRIEVAL_MAX_RESULTS`: Maximum number of results to return after filtering (default: 3)
- `RETRIEVAL_ENABLE_QUERY_EXPANSION`: Enable automatic query expansion with domain variants (default: true)
- `RETRIEVAL_FALLBACK_TO_KEYWORD`: Use keyword matching when semantic models unavailable (default: true)

#### External Query API Configuration
- `EXTERNAL_QUERY_ENABLED`: Enable/disable external query API calls (default: true)
- `EXTERNAL_QUERY_API_URL`: URL for external query API (default: http://192.168.50.90:5401/)
- `EXTERNAL_QUERY_TIMEOUT`: Timeout for external API calls in seconds (default: 10)

#### Query Refinement Configuration
- `QUERY_REFINEMENT_ENABLED`: Enable/disable AI-powered query refinement (default: true)
- `QUERY_REFINEMENT_TEMPERATURE`: Temperature for query refinement AI model (default: 0.3)

#### Application Configuration
- `LOG_LEVEL`: Logging level (default: INFO, options: DEBUG, INFO, WARNING, ERROR)
- `DEBUG_MODE`: Enable debug mode for additional logging (default: false)

### Configuration Examples

#### High-Performance Setup with Enhanced Retrieval
```bash
GRAPHITI_MAX_NODES=5
GRAPHITI_MAX_FACTS=20
EXTERNAL_QUERY_ENABLED=true
QUERY_REFINEMENT_ENABLED=true
# Enhanced retrieval settings for maximum relevance
RETRIEVAL_RELEVANCE_THRESHOLD=0.3
RETRIEVAL_MAX_RESULTS=5
RETRIEVAL_ENABLE_QUERY_EXPANSION=true
```

#### Balanced Setup (Recommended)
```bash
GRAPHITI_MAX_NODES=3
GRAPHITI_MAX_FACTS=15
EXTERNAL_QUERY_ENABLED=true
QUERY_REFINEMENT_ENABLED=true
# Default enhanced retrieval settings work well
RETRIEVAL_RELEVANCE_THRESHOLD=0.25
RETRIEVAL_MAX_RESULTS=3
```

#### Minimal Setup (Less Context, Faster)
```bash
GRAPHITI_MAX_NODES=1
GRAPHITI_MAX_FACTS=3
EXTERNAL_QUERY_ENABLED=false
RETRIEVAL_RELEVANCE_THRESHOLD=0.2
RETRIEVAL_MAX_RESULTS=2
QUERY_REFINEMENT_ENABLED=false
```

#### Balanced Setup (Recommended)
```bash
GRAPHITI_MAX_NODES=2
GRAPHITI_MAX_FACTS=10
EXTERNAL_QUERY_ENABLED=true
QUERY_REFINEMENT_ENABLED=true
QUERY_REFINEMENT_TEMPERATURE=0.3
```

#### Custom Weighting for Recent Messages
```bash
GRAPHITI_WEIGHT_LAST_MESSAGE=0.8
GRAPHITI_WEIGHT_PREVIOUS_ASSISTANT_MESSAGE=0.15
GRAPHITI_WEIGHT_PRIOR_USER_MESSAGE=0.05
```

#### BigQuery GDELT Configuration
```bash
# Enable/disable BigQuery integration
BIGQUERY_ENABLED=true

# Default GDELT query type (1, 2, or 3)
BIGQUERY_DEFAULT_EXAMPLE=3

# Maximum context length for BigQuery results
BIGQUERY_MAX_CONTEXT_LENGTH=8000
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

- `POST /webhook/letta`: Receives webhooks from Letta, retrieves context from Graphiti, and returns it.

## Troubleshooting

If you encounter connection issues with Graphiti:

1. Ensure the Graphiti API is running and accessible from the container
2. Check network settings in the Docker Compose file
3. Verify the GRAPHITI_URL environment variable is correctly set
4. Run the service standalone for testing: `python flask_webhook_receiver.py`

### BigQuery Authentication

For BigQuery GDELT integration to work, you need Google Cloud authentication:

**Option A: Application Default Credentials (Recommended)**
```bash
# Install Google Cloud SDK and authenticate
gcloud auth application-default login
```

**Option B: Service Account Key File**
```bash
# Set environment variable pointing to your service account key
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/keyfile.json"
```

Note: GDELT is a public dataset, so you only need basic Google Cloud authentication. No special permissions required.

### Testing BigQuery Integration

```bash
# Test BigQuery functionality directly
python test_bigquery_integration.py direct

# Demo the webhook integration (requires webhook server running)
python demo_bigquery_webhook.py
```

## Docker Hub Repository

The Docker image is available at: [oculair/letta-webhook-receiver](https://hub.docker.com/r/oculair/letta-webhook-receiver)