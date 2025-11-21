# Suggested Commands for Development

## Running the Application

### Local Development
```bash
# Using Python directly
python run_server.py --host 0.0.0.0 --port 5005

# Using the app module directly
python -m webhook_server.app --host 0.0.0.0 --port 5005
```

### Docker Compose
```bash
# Local development (port 5005)
docker-compose -f docker-compose-local.yml up -d
docker-compose -f docker-compose-local.yml logs -f
docker-compose -f docker-compose-local.yml down

# Production deployment
docker-compose -f compose-prod.yaml --env-file .env.prod up -d
docker-compose -f compose-prod.yaml logs -f
docker-compose -f compose-prod.yaml down

# Using convenience scripts
./run-webhook-service.sh  # Linux/macOS
run-webhook-service.bat   # Windows
```

### Docker Build
```bash
# Build image
docker build -t letta-webhook-receiver -f Dockerfile .

# Build with specific variant
docker build -t letta-webhook-receiver:light -f Dockerfile.light .
docker build -t letta-webhook-receiver:prod -f Dockerfile.production .
```

## Testing

### Run Tests
```bash
# Run specific test files
python test_webhook.py
python test_bigquery_integration.py
python test_arxiv_integration.py
python test_graphiti_connection.py

# Run simulation suite
python simulation_suite.py
python run_large_simulation.py
```

### Debug Scripts
```bash
# Test specific integrations
python test_gdelt_webhook_integration.py
python test_complete_webhook_flow.py
python debug_webhook_data.py
python verify_fix.py
```

## Development Utilities

### Check API Connections
```bash
# Test Graphiti connection
python test_graphiti_connection.py

# Test Letta API
python test_memory_block_operations.py

# Test BigQuery GDELT
python query_gdelt.py
```

### Monitoring
```bash
# Monitor simulation progress
python monitor_simulation.py

# Check health endpoint
curl http://localhost:5005/health
```

## Environment Setup

### Install Dependencies
```bash
# Full installation
pip install -r requirements.txt

# Light installation (without heavy ML dependencies)
pip install -r requirements-light.txt
```

### Environment Variables
Create a `.env` or `.env.prod` file with required variables (see compose files for examples)

## Linux System Commands
Standard Linux commands are available:
- `ls -la` - List files with details
- `cat`, `head`, `tail` - View file contents
- `grep` - Search in files
- `find` - Find files
- `git` - Version control operations
- `docker`, `docker-compose` - Container management
