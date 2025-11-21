# Webhook 500 Error Troubleshooting Guide

## Problem
The webhook receiver is returning HTTP 500 errors when receiving POST requests to `/webhook/letta`.

## Diagnosis Steps

### Step 1: Stop Current Container and Run Debug Version

```bash
# Stop the current container
docker-compose down

# Build and run the debug version
docker-compose -f compose-debug.yaml up --build
```

### Step 2: Test the Debug Endpoints

```bash
# Test health endpoint
curl http://localhost:5005/health

# Test debug endpoint (shows detailed import status)
curl http://localhost:5005/debug

# Or use the test script
python test_webhook.py
```

### Step 3: Check Import Status

The debug version will show which modules are failing to import. Common issues:

1. **Missing dependencies**: Check if all packages in `requirements.txt` are installed
2. **Cerebras SDK issues**: The `cerebras-cloud-sdk` might have compatibility issues
3. **Sentence transformers**: Large download, might fail in container
4. **Environment variables**: Missing required API keys or URLs

### Step 4: Check Container Logs

```bash
# View detailed logs from debug container
docker-compose -f compose-debug.yaml logs -f webhook-receiver-debug
```

## Common Issues and Solutions

### Issue 1: Import Errors

**Symptoms**: Import status shows ❌ for key modules

**Solutions**:
- Check if all dependencies are properly installed
- Verify Python version compatibility
- Check for missing system dependencies

### Issue 2: Environment Variable Issues

**Symptoms**: Environment shows "NOT_SET" for required variables

**Solutions**:
- Ensure `.env.prod` or environment variables are properly set
- Check docker-compose environment section
- Verify API keys are valid

### Issue 3: Network Connectivity

**Symptoms**: Health check passes but webhook fails during API calls

**Solutions**:
- Check if Graphiti API is accessible from container: `http://192.168.50.90:8001/api`
- Check if Letta API is accessible: `https://letta2.oculair.ca`
- Verify firewall/network settings

### Issue 4: Memory/Resource Issues

**Symptoms**: Container starts but crashes during processing

**Solutions**:
- Increase container memory limits
- Disable optional features like sentence transformers
- Use simpler retrieval methods

## Quick Fixes

### Fix 1: Disable Optional Features

Edit `compose-debug.yaml` and add:
```yaml
environment:
  - EXTERNAL_QUERY_ENABLED=false
  - QUERY_REFINEMENT_ENABLED=false
```

### Fix 2: Use Minimal Requirements

Create `requirements-minimal.txt`:
```
flask==3.0.0
requests==2.31.0
python-dotenv==1.0.0
```

Update `Dockerfile.debug` to use minimal requirements temporarily.

### Fix 3: Test Without Dependencies

The debug version includes fallback functions that work without external dependencies.

## Testing Commands

```bash
# Test simple prompt
curl -X POST http://localhost:5005/webhook/letta \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test message"}'

# Test Letta format
curl -X POST http://localhost:5005/webhook/letta \
  -H "Content-Type: application/json" \
  -d '{
    "request": {
      "body": {
        "messages": [{"role": "user", "content": "test"}]
      },
      "path": "/v1/agents/agent-test/messages"
    }
  }'
```

## Expected Debug Output

When working correctly, you should see:
```
🔍 Testing all imports...
  flask: ✅ OK - version 3.0.0
  requests: ✅ OK - version 2.31.0
  production_improved_retrieval: ✅ OK
  tool_manager: ✅ OK
  cerebras_client: ✅ OK
  sentence_transformers: ✅ OK
```

## Recovery Steps

1. **If imports fail**: Use the minimal requirements approach
2. **If API calls fail**: Check network connectivity and credentials
3. **If memory issues**: Disable optional features and use basic retrieval
4. **If all else fails**: The debug version provides detailed error traces to identify the root cause

## Next Steps

Once you identify the specific error from the debug output:

1. **Import errors**: Fix dependencies or use fallbacks
2. **API errors**: Fix credentials or network issues  
3. **Processing errors**: Review the detailed traceback in debug output

The debug version is designed to be more resilient and provide detailed diagnostics to help identify the exact cause of the 500 error.