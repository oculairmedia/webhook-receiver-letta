"""FastMCP server exposing agent registry search capability."""

from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager
from typing import Literal

import requests
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

LOGGER = logging.getLogger(__name__)

INSTRUCTIONS = """\
Call the `find_agents` tool to search for relevant agents in the agent registry.
Provide a search query describing what kind of agent you're looking for.
The tool returns a list of agents with their IDs, capabilities, and relevance scores.
"""

mcp = FastMCP(name="agent-registry", instructions=INSTRUCTIONS)

# Configuration
AGENT_REGISTRY_URL = os.environ.get("AGENT_REGISTRY_URL", "http://localhost:8021")
DEFAULT_MAX_AGENTS = int(os.environ.get("AGENT_REGISTRY_MAX_AGENTS", "10"))
DEFAULT_MIN_SCORE = float(os.environ.get("AGENT_REGISTRY_MIN_SCORE", "0.3"))


@contextmanager
def _metric_scope(kind: Literal["tool", "resource"]) -> None:
    """Record execution duration for telemetry metrics."""
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        LOGGER.info(f"{kind} execution took {duration_ms:.2f}ms")


@mcp.tool(
    name="find_agents",
    description="Search for relevant agents in the agent registry to find collaborators or specialists. Returns a list of agents with their IDs, capabilities, and relevance scores."
)
async def find_agents(
    query: str,
    limit: int = 10,
    min_score: float = 0.3
) -> str:
    """
    Search for relevant agents in the agent registry based on a query.
    
    Args:
        query: Search query describing what kind of agent you're looking for 
               (e.g., 'machine learning expert', 'database administrator', 'content writer')
        limit: Maximum number of agents to return (default: 10, max: 50)
        min_score: Minimum relevance score 0.0-1.0 (default: 0.3)
    
    Returns:
        Formatted string with agent details including IDs, descriptions, and capabilities
    """
    with _metric_scope("tool"):
        # Validate parameters
        if not query or not query.strip():
            raise ToolError("Query parameter is required and cannot be empty")
        
        if limit < 1 or limit > 50:
            raise ToolError("Limit must be between 1 and 50")
        
        if min_score < 0.0 or min_score > 1.0:
            raise ToolError("min_score must be between 0.0 and 1.0")
        
        # Call agent registry API
        url = f"{AGENT_REGISTRY_URL}/api/v1/agents/search"
        params = {
            "query": query.strip(),
            "limit": limit,
            "min_score": min_score
        }
        
        try:
            LOGGER.info(f"Searching for agents with query: '{query[:100]}...'")
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            result = response.json()
            agents = result.get("agents", [])
            
            if not agents:
                return f"No relevant agents found for query: '{query}'\n\nTry:\n- Broadening your search terms\n- Lowering the min_score parameter\n- Using different keywords"
            
            # Format the results
            output_parts = [
                f"Found {len(agents)} relevant agent{'s' if len(agents) != 1 else ''}:\n"
            ]
            
            for idx, agent in enumerate(agents, 1):
                agent_id = agent.get("agent_id", "unknown")
                name = agent.get("name", "Unknown Agent")
                description = agent.get("description", "No description")
                score = agent.get("score", 0.0)
                status = agent.get("status", "unknown")
                capabilities = agent.get("capabilities", [])
                
                agent_info = f"\n{idx}. **{name}** (ID: `{agent_id}`)"
                agent_info += f"\n   Status: {status}"
                agent_info += f"\n   Relevance: {score:.2f}"
                
                # Truncate description if too long
                if len(description) > 200:
                    agent_info += f"\n   Description: {description[:200]}..."
                else:
                    agent_info += f"\n   Description: {description}"
                
                if capabilities:
                    caps_text = ", ".join(capabilities[:3])
                    if len(capabilities) > 3:
                        caps_text += f" (+{len(capabilities) - 3} more)"
                    agent_info += f"\n   Capabilities: {caps_text}"
                
                output_parts.append(agent_info)
            
            output_parts.append(
                "\n\n💡 **Tip**: You can message these agents using the `matrix_agent_message` tool with their agent ID."
            )
            
            return "\n".join(output_parts)
            
        except requests.exceptions.Timeout:
            raise ToolError(
                f"Request to agent registry timed out after 15 seconds. "
                f"The service at {AGENT_REGISTRY_URL} may be unavailable."
            )
        except requests.exceptions.ConnectionError:
            raise ToolError(
                f"Could not connect to agent registry at {AGENT_REGISTRY_URL}. "
                f"Please verify the service is running."
            )
        except requests.exceptions.HTTPError as e:
            raise ToolError(
                f"Agent registry returned an error: HTTP {e.response.status_code}. "
                f"Response: {e.response.text[:200]}"
            )
        except Exception as e:
            raise ToolError(f"Unexpected error searching for agents: {str(e)}")


@mcp.resource(
    "agent-registry://stats",
    name="Agent Registry Statistics",
    description="Get statistics about the agent registry",
    mime_type="application/json"
)
async def get_registry_stats() -> dict:
    """Return statistics about the agent registry."""
    with _metric_scope("resource"):
        try:
            url = f"{AGENT_REGISTRY_URL}/api/v1/stats"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                "error": str(e),
                "registry_url": AGENT_REGISTRY_URL
            }


def main() -> None:
    """Entrypoint for running the FastMCP server over HTTP transport."""
    port = int(os.environ.get("AGENT_REGISTRY_MCP_PORT", "8022"))
    
    log_level = os.environ.get("AGENT_REGISTRY_MCP_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    LOGGER.info(f"Starting Agent Registry FastMCP server on port {port}")
    LOGGER.info(f"Agent Registry URL: {AGENT_REGISTRY_URL}")
    
    # SSE is the HTTP transport for MCP (Server-Sent Events over HTTP)
    # Set host and port via environment variables for uvicorn
    os.environ["UVICORN_HOST"] = "0.0.0.0"
    os.environ["UVICORN_PORT"] = str(port)
    
    mcp.run(transport="sse")


if __name__ == "__main__":
    main()
