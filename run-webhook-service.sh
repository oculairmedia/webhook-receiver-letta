#!/bin/bash
# Script to run the Letta Webhook Receiver service using Docker Compose

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
    echo "Warning: .env.prod file not found. Using default environment variables."
    echo "Consider creating a .env.prod file for production settings."
fi

# Pull the latest image
echo "Pulling the latest image from Docker Hub..."
docker pull oculair/letta-webhook-receiver:latest

# Run the service
echo "Starting the Letta Webhook Receiver service..."
docker compose -f compose-prod.yaml --env-file .env.prod up -d

echo "Service started! You can check logs with:"
echo "docker compose -f compose-prod.yaml logs -f"
echo ""
echo "To stop the service:"
echo "docker compose -f compose-prod.yaml down"