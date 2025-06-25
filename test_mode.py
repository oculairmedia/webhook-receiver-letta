#!/usr/bin/env python3
"""
Test mode script for flask_webhook_receiver.py

This script tests the agent identity retrieval functionality by:
1. Simulating a webhook request with a sample agent ID
2. Using the Letta API to retrieve agent information directly
"""

import argparse
import json
import os
import sys
import requests
from typing import Dict, Any, Optional

# Default configuration
LETTA_BASE_URL = os.environ.get("LETTA_BASE_URL", "https://letta2.oculair.ca")
LETTA_PASSWORD = os.environ.get("LETTA_PASSWORD", "lettaSecurePass123")
LETTA_API_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-BARE-PASSWORD": f"password {LETTA_PASSWORD}",
    "Authorization": f"Bearer {LETTA_PASSWORD}"
}

def get_api_url(path: str) -> str:
    """Construct API URL following Letta's v1 convention."""
    base = f"{LETTA_BASE_URL}/v1".rstrip("/")
    path = path.lstrip("/")
    return f"{base}/{path}"

def retrieve_agent_info(agent_id: str) -> Dict[str, Any]:
    """
    Retrieve agent information using the Letta API.
    
    Args:
        agent_id: The agent ID to retrieve
        
    Returns:
        The agent information as a dictionary
    """
    try:
        # Prepare headers with user_id
        headers = {**LETTA_API_HEADERS, "user_id": agent_id}
        
        # Make the request to retrieve agent information
        agent_url = get_api_url(f"agents/{agent_id}")
        print(f"Retrieving agent information from: {agent_url}")
        
        response = requests.get(agent_url, headers=headers, timeout=10)
        print(f"Response status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            return {"error": f"Failed to retrieve agent information: {response.status_code}"}
        
        # Parse and return the response
        agent_info = response.json()
        return agent_info
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
        return {"error": str(e)}
    except json.JSONDecodeError:
        print(f"Failed to parse response as JSON: {response.text}")
        return {"error": "Invalid JSON response"}

def retrieve_agent_identity(agent_id: str) -> Dict[str, Any]:
    """
    Retrieve agent identity information using the Letta API.
    
    Args:
        agent_id: The agent ID to retrieve identity for
        
    Returns:
        The identity information as a dictionary
    """
    try:
        # Step 1: Get agent information to retrieve identity IDs
        agent_info = retrieve_agent_info(agent_id)
        
        if "error" in agent_info:
            return {"error": f"Failed to retrieve agent information: {agent_info['error']}"}
        
        # Step 2: Extract identity IDs from agent information
        identity_ids = agent_info.get("identity_ids", [])
        
        if not identity_ids:
            return {"error": "No identity IDs found in agent information"}
        
        print(f"Found {len(identity_ids)} identity IDs: {', '.join(identity_ids)}")
        
        # Step 3: Retrieve identity information for each identity ID
        identities = []
        for identity_id in identity_ids:
            # Prepare headers
            headers = LETTA_API_HEADERS.copy()
            
            # Make the request to retrieve identity information
            identity_url = get_api_url(f"identities/{identity_id}")
            print(f"Retrieving identity information from: {identity_url}")
            
            response = requests.get(identity_url, headers=headers, timeout=10)
            print(f"Response status code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error response: {response.text}")
                continue  # Skip this identity and try the next one
            
            # Parse the response
            identity_info = response.json()
            identities.append(identity_info)
        
        if not identities:
            return {"error": "Failed to retrieve any identity information"}
            
        return identities if len(identities) > 1 else identities[0]
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
        return {"error": str(e)}
    except json.JSONDecodeError:
        print(f"Failed to parse response as JSON: {response.text}")
        return {"error": "Invalid JSON response"}
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {"error": str(e)}

def simulate_webhook_request(agent_id: str) -> Dict[str, Any]:
    """
    Simulate a webhook request with the given agent ID.
    
    Args:
        agent_id: The agent ID to include in the request
        
    Returns:
        A dictionary representing the webhook request
    """
    # Create a sample webhook request payload
    webhook_payload = {
        "prompt": "Test prompt for identity retrieval",
        "max_nodes": 3,
        "max_facts": 5,
        "request": {
            "path": f"/v1/agents/{agent_id}/messages/stream",
            "body": {
                "messages": [
                    {
                        "role": "user",
                        "content": "Test prompt for identity retrieval"
                    }
                ]
            }
        }
    }
    
    return webhook_payload

def extract_agent_id_from_path(path: str) -> Optional[str]:
    """
    Extract the agent ID from a request path.
    
    Args:
        path: The request path
        
    Returns:
        The extracted agent ID, or None if not found
    """
    print(f"Extracting agent ID from path: {path}")
    
    if "agents" in path:
        parts = path.split("/")
        try:
            agents_index = parts.index("agents")
            if len(parts) > agents_index + 1:
                potential_agent_id = parts[agents_index + 1]
                if potential_agent_id.startswith("agent-"):
                    print(f"Successfully extracted agent ID: {potential_agent_id}")
                    return potential_agent_id
                else:
                    print(f"Segment '{potential_agent_id}' does not start with 'agent-'")
            else:
                print("Not enough segments after 'agents' to be an agent ID")
        except ValueError:
            print("'agents' segment not found in path parts")
    else:
        print("'agents' substring not found in path")
    
    return None

def run_test(agent_id: str, verbose: bool = False) -> None:
    """
    Run the test for agent identity retrieval.
    
    Args:
        agent_id: The agent ID to test
        verbose: Whether to print verbose output
    """
    print("\n" + "="*80)
    print(f"TESTING AGENT IDENTITY RETRIEVAL FOR: {agent_id}")
    print("="*80)
    
    # Step 1: Simulate a webhook request
    webhook_payload = simulate_webhook_request(agent_id)
    if verbose:
        print("\nSimulated webhook payload:")
        print(json.dumps(webhook_payload, indent=2))
    
    # Step 2: Extract the agent ID from the request path
    request_path = webhook_payload.get("request", {}).get("path", "")
    extracted_agent_id = extract_agent_id_from_path(request_path)
    
    if extracted_agent_id != agent_id:
        print(f"WARNING: Extracted agent ID '{extracted_agent_id}' does not match expected '{agent_id}'")
    
    # Step 3: Retrieve agent information
    print("\nRetrieving agent information...")
    agent_info = retrieve_agent_info(agent_id)
    
    if "error" in agent_info:
        print(f"Error retrieving agent information: {agent_info['error']}")
    else:
        print("\nAgent Information:")
        if verbose:
            print(json.dumps(agent_info, indent=2))
        else:
            # Print a summary of the agent information
            print(f"  ID: {agent_info.get('id')}")
            print(f"  Name: {agent_info.get('name')}")
            print(f"  Type: {agent_info.get('agent_type')}")
    
    # Step 4: Retrieve identity information using the identity IDs from agent_info
    print("\nRetrieving identity information...")
    identity_info = retrieve_agent_identity(agent_id)
    
    if "error" in identity_info:
        print(f"Error retrieving identity information: {identity_info['error']}")
    else:
        print("\nIdentity Information:")
        if verbose:
            print(json.dumps(identity_info, indent=2))
        else:
            # Print a summary of the identity information
            if isinstance(identity_info, list):
                for i, identity in enumerate(identity_info):
                    print(f"  Identity {i+1}:")
                    print(f"    ID: {identity.get('id')}")
                    print(f"    Name: {identity.get('name')}")
                    print(f"    Type: {identity.get('identity_type')}")
                    print(f"    Identifier Key: {identity.get('identifier_key')}")
                    
                    # Print properties if available
                    properties = identity.get('properties', [])
                    if properties:
                        print(f"    Properties:")
                        for prop in properties:
                            print(f"      {prop.get('key')}: {prop.get('value')} ({prop.get('type')})")
            elif isinstance(identity_info, dict):
                print(f"  ID: {identity_info.get('id')}")
                print(f"  Name: {identity_info.get('name')}")
                print(f"  Type: {identity_info.get('identity_type')}")
                print(f"  Identifier Key: {identity_info.get('identifier_key')}")
                
                # Print properties if available
                properties = identity_info.get('properties', [])
                if properties:
                    print(f"  Properties:")
                    for prop in properties:
                        print(f"    {prop.get('key')}: {prop.get('value')} ({prop.get('type')})")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

def main():
    parser = argparse.ArgumentParser(description="Test agent identity retrieval")
    parser.add_argument(
        "--agent-id", 
        type=str, 
        default="agent-0e99d1a5-d9ca-43b0-9df9-c09761d01444",
        help="The agent ID to test"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Print verbose output"
    )
    
    args = parser.parse_args()
    run_test(args.agent_id, args.verbose)

if __name__ == "__main__":
    main()