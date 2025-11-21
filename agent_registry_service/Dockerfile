FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
COPY requirements-mcp.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY ollama_embeddings.py .
COPY sync_service.py .
COPY mcp_server.py .

# Expose port
EXPOSE 8021

# Health check - only for main app.py service
# Override or disable in compose.yaml for other services (sync, mcp)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8021/health', timeout=5)" || exit 1

# Run the application
CMD ["python", "app.py"]
