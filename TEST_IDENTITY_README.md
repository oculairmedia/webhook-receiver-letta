# Agent Identity Retrieval Testing

This directory contains scripts to test the agent identity retrieval functionality in `flask_webhook_receiver.py`.

## Background

The `flask_webhook_receiver.py` script processes webhooks from Letta, extracts the agent ID from the request path, and retrieves the agent's identity information. This functionality was recently fixed, and these test scripts help verify that the fix is working correctly.

The identity retrieval process follows these steps:
1. Extract the agent ID from the request path
2. Retrieve the agent information using the Letta API
3. Extract the identity IDs from the agent information
4. Retrieve the identity information for each identity ID

## Test Scripts

### 1. test_agent_identity.py

This script provides two methods for testing agent identity retrieval:

1. **Webhook Method**: Sends a simulated webhook request to the running `flask_webhook_receiver.py` server
2. **Direct API Method**: Directly retrieves agent and identity information using the Letta API

#### Usage

```bash
# Test both methods
python test_agent_identity.py --agent-id agent-0e99d1a5-d9ca-43b0-9df9-c09761d01444 --verbose

# Test only the webhook method
python test_agent_identity.py --method webhook --agent-id agent-0e99d1a5-d9ca-43b0-9df9-c09761d01444 --verbose

# Test only the direct API method
python test_agent_identity.py --method direct --agent-id agent-0e99d1a5-d9ca-43b0-9df9-c09761d01444 --verbose
```

### 2. test_mode.py

This script focuses on testing the agent identity retrieval using the direct API method. It simulates the webhook request path extraction and then retrieves agent and identity information directly from the Letta API.

#### Usage

```bash
# Run with default agent ID
python test_mode.py --verbose

# Run with a specific agent ID
python test_mode.py --agent-id agent-0e99d1a5-d9ca-43b0-9df9-c09761d01444 --verbose
```

## How to Run the Tests

### Prerequisites

1. Make sure you have the required dependencies installed:
   ```bash
   pip install requests flask
   ```

2. Ensure that the environment variables are properly set up:
   - `LETTA_BASE_URL`: The base URL of the Letta API (default: "https://letta2.oculair.ca")
   - `LETTA_PASSWORD`: The password for the Letta API (default: "lettaSecurePass123")

### Option 1: Test with a Running Flask Server

1. Start the Flask server:
   ```bash
   python flask_webhook_receiver.py --port 5005
   ```

2. In a separate terminal, run the test script with the webhook method:
   ```bash
   python test_agent_identity.py --method webhook --verbose
   ```

### Option 2: Direct API Testing (No Server Required)

Run the direct test method:
```bash
python test_agent_identity.py --method direct --verbose
```

Or use the test_mode.py script:
```bash
python test_mode.py --verbose
```

## Expected Output

The test scripts will display:
1. The agent ID extraction process (for webhook method)
2. The agent information retrieval process, including identity IDs
3. The identity information retrieval process for each identity ID
4. Detailed summaries of the retrieved information, including:
   - Identity ID, name, and type
   - Identifier key
   - Properties (if available)

A successful test will show the agent ID, agent name, and identity details (if available) in the terminal output.

## Troubleshooting

- If you encounter import errors, make sure you're running the scripts from the same directory as `flask_webhook_receiver.py`.
- If you get connection errors in webhook method, verify that the Flask server is running and accessible at the specified URL.
- If you get connection errors in direct API method, verify that the Letta API is accessible and that your credentials are correct.
- If the identity information is not being retrieved, check that the agent ID is valid and that the agent has associated identity IDs in its configuration.
- The scripts now use the `/v1/identities/{identity_id}` endpoint to retrieve identity information, rather than the `/v1/agents/{agent_id}/identity` endpoint which may return a 404 error.

## Notes

- The default agent ID is set to `agent-0e99d1a5-d9ca-43b0-9df9-c09761d01444`.
- You can specify a different agent ID using the `--agent-id` parameter.
- Use the `--verbose` flag to see more detailed output, including the full request payloads and responses.