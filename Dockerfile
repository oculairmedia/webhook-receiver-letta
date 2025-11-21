# Production Dockerfile for the refactored webhook server
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements-light.txt .
RUN pip install --no-cache-dir -r requirements-light.txt

# Copy the new application directory
COPY webhook_server/ /app/webhook_server

# Copy other necessary files
COPY arxiv_integration.py .
COPY tool_manager.py .
COPY letta_tool_utils.py .

# Expose port
EXPOSE 8290

# Health check (optional, but good practice)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8290/health', timeout=5)" || exit 1

# Run the application
CMD ["python", "-m", "webhook_server.app", "--host", "0.0.0.0", "--port", "8290"]