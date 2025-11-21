#!/bin/bash

# Agent Registry Service Startup Script

echo "Starting Agent Registry Service..."

# Check if running in Docker
if [ -f /.dockerenv ]; then
    echo "Running in Docker container"
    python app.py
else
    echo "Running locally"
    
    # Check if Weaviate is running
    if ! curl -s http://localhost:8080/v1/meta > /dev/null 2>&1; then
        echo "WARNING: Weaviate not detected at http://localhost:8080"
        echo "Starting Weaviate with docker-compose..."
        docker-compose up -d weaviate
        
        # Wait for Weaviate to be ready
        echo "Waiting for Weaviate to be ready..."
        for i in {1..30}; do
            if curl -s http://localhost:8080/v1/meta > /dev/null 2>&1; then
                echo "Weaviate is ready!"
                break
            fi
            echo "Waiting... ($i/30)"
            sleep 2
        done
    else
        echo "Weaviate is already running"
    fi
    
    # Set environment variables if not set
    export WEAVIATE_URL="${WEAVIATE_URL:-http://localhost:8080}"
    export EMBEDDING_MODEL="${EMBEDDING_MODEL:-all-MiniLM-L6-v2}"
    export PORT="${PORT:-8020}"
    
    echo "Configuration:"
    echo "  WEAVIATE_URL: $WEAVIATE_URL"
    echo "  EMBEDDING_MODEL: $EMBEDDING_MODEL"
    echo "  PORT: $PORT"
    echo ""
    
    # Start the service
    python app.py
fi
