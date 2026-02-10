import os

# Default configuration
LETTA_BASE_URL = os.environ.get("LETTA_BASE_URL", "http://192.168.50.90:8289")
LETTA_PASSWORD = os.environ.get("LETTA_PASSWORD", "lettaSecurePass123")
LETTA_API_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-BARE-PASSWORD": f"password {LETTA_PASSWORD}",
    "Authorization": f"Bearer {LETTA_PASSWORD}"
}

# Graphiti configuration
GRAPHITI_API_URL = os.environ.get("GRAPHITI_URL", "http://192.168.50.90:8001/api")
GRAPHITI_MAX_NODES = int(os.environ.get("GRAPHITI_MAX_NODES", "8"))
GRAPHITI_MAX_FACTS = int(os.environ.get("GRAPHITI_MAX_FACTS", "20"))

# Maximum context snippet length for cumulative context
MAX_CONTEXT_SNIPPET_LENGTH = 6000

# Protected tools configuration
# These tools should always be attached to agents and never detached
# Format: comma-separated list of tool IDs or tool names
# Can be set via environment variable PROTECTED_TOOLS
PROTECTED_TOOLS_DEFAULT = ""  # Empty by default - no forced tools
PROTECTED_TOOLS = os.environ.get("PROTECTED_TOOLS", PROTECTED_TOOLS_DEFAULT)

# Tool attachment configuration
TOOL_ATTACHMENT_MIN_SCORE = float(os.environ.get("TOOL_ATTACHMENT_MIN_SCORE", "50.0"))
TOOL_ATTACHMENT_LIMIT = int(os.environ.get("TOOL_ATTACHMENT_LIMIT", "3"))

def get_api_url(path: str) -> str:
    """Construct API URL following Letta's v1 convention."""
    base = LETTA_BASE_URL.rstrip("/")
    base = f"{base}/v1"
    path = path.lstrip("/")
    return f"{base}/{path}"

def get_graphiti_config():
    """Get Graphiti configuration."""
    return {
        "api_url": GRAPHITI_API_URL,
        "max_nodes": GRAPHITI_MAX_NODES,
        "max_facts": GRAPHITI_MAX_FACTS
    }