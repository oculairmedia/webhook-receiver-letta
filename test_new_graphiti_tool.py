#!/usr/bin/env python3
"""
Test the new Graphiti search nodes tool provided by user
"""

import json
import subprocess
import sys

def test_new_graphiti_tool():
    """Test the new Graphiti search tool with various queries"""
    
    print("🔍 TESTING NEW GRAPHITI SEARCH NODES TOOL")
    print("=" * 60)
    
    # Create the search tool file
    tool_content = '''#!/usr/bin/env python3
"""
Search Nodes Tool - A tool to search for nodes in the Graphiti knowledge graph
"""

import json
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, Optional, Any, Union, List


def graphiti_search_nodes(
    query: str,
    group_ids: Optional[List[str]] = None,  # Default to None
    max_nodes: int = 10,
    center_node_uuid: Optional[str] = None,
    entity: str = "",
    request_heartbeat: bool = False,
) -> str:
    """
    Search the Graphiti knowledge graph for relevant node summaries.

    This function supports two usage scenarios:
      1) Searching for nodes in the knowledge graph
      2) Retrieving the tool's metadata by passing query="__tool_info__"

    Args:
        query: The search query
        group_ids: Optional list of group IDs to filter results
        max_nodes: Maximum number of nodes to return (default: 10)
        center_node_uuid: Optional UUID of a node to center the search around
        entity: Optional single entity type to filter results (permitted: "Preference", "Procedure")
        request_heartbeat: Letta's heartbeat parameter (ignored by this function)

    Returns:
        str: JSON-formatted string containing the response
    """
    if query == "__tool_info__":
        info = {
            "name": "graphiti_search_nodes",
            "description": "Search the Graphiti knowledge graph for relevant node summaries",
            "args": {
                "query": {
                    "type": "str",
                    "description": "The search query",
                    "required": True
                },
                "group_ids": {
                    "type": "list[str]",
                    "description": "Optional list of group IDs to filter results",
                    "required": False
                },
                "max_nodes": {
                    "type": "int",
                    "description": "Maximum number of nodes to return",
                    "required": False,
                    "default": 10
                },
                "center_node_uuid": {
                    "type": "str",
                    "description": "Optional UUID of a node to center the search around",
                    "required": False
                },
                "entity": {
                    "type": "str",
                    "description": "Optional single entity type to filter results (permitted: 'Preference', 'Procedure')",
                    "required": False,
                    "default": ""
                },
                "request_heartbeat": {
                    "type": "bool",
                    "description": "Letta's heartbeat parameter (ignored by this function)",
                    "required": False,
                    "default": False
                }
            }
        }
        return json.dumps(info)

    # Validate max_nodes
    if not isinstance(max_nodes, int) or max_nodes <= 0:
        return json.dumps({"error": f"Invalid max_nodes value: {max_nodes}. Must be a positive integer."})

    base_url = os.environ.get("GRAPHITI_URL", "http://192.168.50.90:8001/api").rstrip("/")

    try:
        session = requests.Session()
        adapter = HTTPAdapter(max_retries=Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        ))
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "query": query,
            "max_nodes": max_nodes,
        }

        if group_ids is None:
            # If agent did not specify group_ids, search all groups.
            # The MCP server interprets an empty list or absence of group_ids (if config.group_id is also None)
            # as search all. Sending an empty list is more explicit for "search all".
            data["group_ids"] = []
        else:
            # If agent specified group_ids (even if it's an empty list itself), use them.
            data["group_ids"] = group_ids
            
        # Add optional parameters if provided
        if center_node_uuid is not None:
            data["center_node_uuid"] = center_node_uuid
        if entity: # entity defaults to "" in function signature
            data["entity"] = entity

        response = session.post(
            f"{base_url}/search/nodes",
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        return json.dumps(response.json())
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Network or HTTP error - {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"Unexpected error - {str(e)}"})
    finally:
        session.close()


if __name__ == "__main__":
    import sys
    # Set up environment with API URL
    os.environ["GRAPHITI_URL"] = "http://192.168.50.90:8001/api"
    
    try:
        # Get input from stdin
        input_data = json.load(sys.stdin)
        
        # Extract known parameters, ignore others
        params = {
            "query": input_data.get("query", "*")
        }
        
        # Only add optional parameters if they exist in input
        if "max_nodes" in input_data:
            params["max_nodes"] = input_data["max_nodes"]
        if "group_ids" in input_data:
            params["group_ids"] = input_data["group_ids"]
        if "center_node_uuid" in input_data:
            params["center_node_uuid"] = input_data["center_node_uuid"]
        if "entity" in input_data:
            params["entity"] = input_data["entity"]
            
        result = graphiti_search_nodes(**params)
        print(result)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
'''
    
    # Write the tool file
    with open("new_graphiti_search_tool.py", "w") as f:
        f.write(tool_content)
    
    # Test queries that should find something
    test_queries = [
        {"query": "emmanuel umukoro", "max_nodes": 50},
        {"query": "emmanuel", "max_nodes": 50},
        {"query": "test", "max_nodes": 50},
        {"query": "resume", "max_nodes": 50},
        {"query": "*", "max_nodes": 50},
        {"query": "", "max_nodes": 50},
        {"query": "Test", "max_nodes": 50}
    ]
    
    for i, test_query in enumerate(test_queries):
        print(f"\n📝 Test {i+1}: {test_query}")
        print("-" * 40)
        
        try:
            # Run the tool with the test query
            result = subprocess.run(
                [sys.executable, "new_graphiti_search_tool.py"],
                input=json.dumps(test_query),
                text=True,
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0:
                try:
                    response_data = json.loads(result.stdout)
                    
                    if "error" in response_data:
                        print(f"❌ Error: {response_data['error']}")
                    else:
                        # Check response structure
                        if isinstance(response_data, dict):
                            if "nodes" in response_data:
                                node_count = len(response_data["nodes"])
                                print(f"✅ Nodes found: {node_count}")
                                if node_count > 0:
                                    print(f"📄 First node preview: {response_data['nodes'][0] if response_data['nodes'] else 'None'}")
                            else:
                                print(f"❓ Unexpected structure: {list(response_data.keys())}")
                        else:
                            print(f"❓ Response is not dict: {type(response_data)}")
                            
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                    print(f"Raw output: {result.stdout}")
            else:
                print(f"❌ Tool failed with return code {result.returncode}")
                print(f"Error: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("❌ Tool execution timed out")
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    print("\n" + "=" * 60)
    print("🔍 COMPARISON: Testing with direct API calls")
    
    # Also test direct API calls for comparison
    import requests
    
    base_url = "http://192.168.50.90:8001/api"
    
    for query_data in test_queries[:3]:  # Test first 3 queries
        query = query_data["query"]
        max_nodes = query_data["max_nodes"]
        
        print(f"\n📡 Direct API test: '{query}'")
        
        payload = {
            "query": query,
            "max_nodes": max_nodes,
            "group_ids": []
        }
        
        try:
            response = requests.post(f"{base_url}/search/nodes", json=payload, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "nodes" in data:
                    print(f"Nodes: {len(data['nodes'])}")
                else:
                    print(f"Structure: {type(data)} - {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Exception: {e}")


if __name__ == "__main__":
    test_new_graphiti_tool()