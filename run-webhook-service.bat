@echo off
REM Script to run the Letta Webhook Receiver service using Docker Compose

REM Check if .env.prod exists
if not exist .env.prod (
    echo Warning: .env.prod file not found. Using default environment variables.
    echo Consider creating a .env.prod file for production settings.
)

REM Pull the latest image
echo Pulling the latest image from Docker Hub...
docker pull oculair/letta-webhook-receiver:latest

REM Run the service
echo Starting the Letta Webhook Receiver service...
docker compose -f compose-prod.yaml --env-file .env.prod up -d

echo Service started! You can check logs with:
echo docker compose -f compose-prod.yaml logs -f
echo.
echo To stop the service:
echo docker compose -f compose-prod.yaml down