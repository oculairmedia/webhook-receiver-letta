#!/usr/bin/env python3
"""
Test script for agent identity retrieval in flask_webhook_receiver.py

This script provides two methods for testing agent identity retrieval:
1. Sending a simulated webhook request to the flask_webhook_receiver.py server
2. Directly retrieving agent and identity information using the Letta API
"""

import argparse
import json
import os
import requests
import sys
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

def send_test_webhook(
    webhook_url: str,
    agent_id: str,
    prompt: str = "Test prompt for identity retrieval",
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Send a test webhook request to the flask_webhook_receiver.py server.
    
    Args:
        webhook_url: The URL of the webhook endpoint (e.g., http://localhost:5005/webhook/letta)
        agent_id: The agent ID to test
        prompt: The prompt to include in the request
        verbose: Whether to print verbose debug information
        
    Returns:
        The JSON response from the webhook endpoint
    """
    # Construct a sample payload that mimics what Letta would send
    payload = {
        "prompt": prompt,
        "max_nodes": 3,
        "max_facts": 5,
        "request": {
            "path": f"/v1/agents/{agent_id}/messages/stream",
            "body": {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        }
    }
    
    if verbose:
        print(f"\nSending webhook request to: {webhook_url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
    
    # Send the request
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        response = requests.post(webhook_url, json=payload, headers=headers)
        
        # Print response details
        print(f"\nResponse Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error Response: {response.text}")
            return {"error": f"Request failed with status code {response.status_code}"}
        
        # Parse and return the JSON response
        response_data = response.json()
        return response_data
    
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {str(e)}")
        return {"error": str(e)}
    except json.JSONDecodeError:
        print(f"Failed to parse response as JSON: {response.text}")
        return {"error": "Invalid JSON response"}

def retrieve_agent_info(agent_id: str, verbose: bool = False) -> Dict[str, Any]:
    """
    Retrieve agent information using the Letta API.
    
    Args:
        agent_id: The agent ID to retrieve
        verbose: Whether to print verbose debug information
        
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
        
        if verbose:
            print("\nAgent Information:")
            print(json.dumps(agent_info, indent=2))
            
        return agent_info
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
        return {"error": str(e)}
    except json.JSONDecodeError:
        print(f"Failed to parse response as JSON: {response.text}")
        return {"error": "Invalid JSON response"}

def retrieve_agent_identity(agent_id: str, verbose: bool = False) -> Dict[str, Any]:
    """
    Retrieve agent identity information using the Letta API.
    
    Args:
        agent_id: The agent ID to retrieve identity for
        verbose: Whether to print verbose debug information
        
    Returns:
        The identity information as a dictionary
    """
    try:
        # Step 1: Get agent information to retrieve identity IDs
        agent_info = retrieve_agent_info(agent_id, verbose=False)
        
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
            
            if verbose:
                print(f"\nIdentity Information for {identity_id}:")
                print(json.dumps(identity_info, indent=2))
                
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

def print_identity_info(response_data: Dict[str, Any]) -> None:
    """
    Extract and print the identity information from the response.
    
    Args:
        response_data: The JSON response from the webhook endpoint
    """
    print("\n" + "="*50)
    print("AGENT IDENTITY INFORMATION")
    print("="*50)
    
    # Check if the response contains an error
    if "error" in response_data:
        print(f"Error: {response_data['error']}")
        return
    
    # Extract agent information
    agent_id = response_data.get("agent_id")
    agent_name = response_data.get("agent_name")
    
    print(f"Agent ID: {agent_id}")
    print(f"Agent Name: {agent_name}")
    
    # Extract identity information
    identity_fields = [
        ("identity_id", "Identity ID"),
        ("identity_name", "Identity Name"),
        ("identity_email", "Identity Email"),
        ("identity_username", "Identity Username"),
        ("identity_user_id", "Identity User ID")
    ]
    
    print("\nIdentity Details:")
    identity_found = False
    
    for field_key, field_label in identity_fields:
        if field_key in response_data:
            print(f"  {field_label}: {response_data[field_key]}")
            identity_found = True
    
    if not identity_found:
        print("  No identity information found in the response.")
    
    print("="*50)

def test_webhook_method(agent_id: str, webhook_url: str, prompt: str, verbose: bool) -> None:
    """
    Test agent identity retrieval using the webhook method.
    
    Args:
        agent_id: The agent ID to test
        webhook_url: The URL of the webhook endpoint
        prompt: The prompt to include in the request
        verbose: Whether to print verbose debug information
    """
    print("\n" + "="*80)
    print(f"TESTING AGENT IDENTITY RETRIEVAL VIA WEBHOOK: {agent_id}")
    print("="*80)
    
    # Send a test webhook request
    response_data = send_test_webhook(
        webhook_url=webhook_url,
        agent_id=agent_id,
        prompt=prompt,
        verbose=verbose
    )
    
    # Print the identity information
    print_identity_info(response_data)

def test_direct_method(agent_id: str, verbose: bool) -> None:
    """
    Test agent identity retrieval using the direct API method.
    
    Args:
        agent_id: The agent ID to test
        verbose: Whether to print verbose debug information
    """
    print("\n" + "="*80)
    print(f"TESTING AGENT IDENTITY RETRIEVAL VIA DIRECT API: {agent_id}")
    print("="*80)
    
    # Step 1: Retrieve agent information
    agent_info = retrieve_agent_info(agent_id, verbose)
    
    if "error" in agent_info:
        print(f"Error retrieving agent information: {agent_info['error']}")
    else:
        print("\nAgent Information Summary:")
        print(f"  ID: {agent_info.get('id')}")
        print(f"  Name: {agent_info.get('name')}")
        print(f"  Type: {agent_info.get('agent_type')}")
        
        # Check for identity_ids in agent_info
        identity_ids = agent_info.get('identity_ids', [])
        if identity_ids:
            print(f"  Identity IDs: {', '.join(identity_ids)}")
        else:
            print("  No identity IDs found in agent information")
    
    # Step 2: Retrieve identity information using the identity IDs from agent_info
    identity_info = retrieve_agent_identity(agent_id, verbose)
    
    if "error" in identity_info:
        print(f"Error retrieving identity information: {identity_info['error']}")
    else:
        print("\nIdentity Information Summary:")
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
    print("DIRECT API TEST COMPLETE")
    print("="*80)

def main():
    parser = argparse.ArgumentParser(description="Test agent identity retrieval in flask_webhook_receiver.py")
    parser.add_argument(
        "--agent-id", 
        type=str, 
        default="agent-0e99d1a5-d9ca-43b0-9df9-c09761d01444",
        help="The agent ID to test"
    )
    parser.add_argument(
        "--url", 
        type=str, 
        default="http://localhost:5005/webhook/letta",
        help="The URL of the webhook endpoint"
    )
    parser.add_argument(
        "--prompt", 
        type=str, 
        default="Test prompt for identity retrieval",
        help="The prompt to include in the request"
    )
    parser.add_argument(
        "--method",
        type=str,
        choices=["webhook", "direct", "both"],
        default="both",
        help="The method to use for testing (webhook, direct, or both)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Print verbose debug information"
    )
    
    args = parser.parse_args()
    
    if args.method in ["webhook", "both"]:
        test_webhook_method(args.agent_id, args.url, args.prompt, args.verbose)
    
    if args.method in ["direct", "both"]:
        test_direct_method(args.agent_id, args.verbose)

if __name__ == "__main__":
    main()