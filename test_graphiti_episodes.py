#!/usr/bin/env python3

import requests
import json
import os

GRAPHITI_API_URL = os.environ.get("GRAPHITI_URL", "http://192.168.50.90:8001/api")

def check_episodes():
    """Check what episodes exist in Graphiti"""
    try:
        url = f"{GRAPHITI_API_URL}/episodes"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            episodes = data.get('episodes', [])
            print(f"Found {len(episodes)} episodes")
            
            for i, episode in enumerate(episodes[:5]):  # Show first 5
                print(f"Episode {i+1}:")
                print(f"  ID: {episode.get('uuid', 'N/A')}")
                print(f"  Name: {episode.get('name', 'N/A')}")
                print(f"  Source: {episode.get('source', 'N/A')}")
                print(f"  Content length: {len(str(episode.get('content', '')))}")
                print()
        else:
            print(f"Error getting episodes: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error checking episodes: {e}")

def test_add_episode():
    """Test adding a new episode to see if the system is working"""
    try:
        url = f"{GRAPHITI_API_URL}/episodes"
        
        episode_data = {
            "name": "test_episode_from_webhook_fix",
            "content": "This is a test episode to verify that Graphiti can accept new data. The user has been working on improving the meridian agent and the graphiti context should now be updating properly.",
            "source": "test",
            "source_description": "Testing episode creation from webhook troubleshooting"
        }
        
        print(f"Attempting to add episode to: {url}")
        response = requests.post(url, json=episode_data, timeout=30)
        
        print(f"Add episode status: {response.status_code}")
        
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            print(f"Successfully added episode: {result}")
            
            # Now check if we can search for it
            print("\nTesting search after adding episode...")
            search_url = f"{GRAPHITI_API_URL}/search/nodes"
            search_payload = {
                "query": "meridian agent",
                "max_nodes": 5,
                "group_ids": []
            }
            
            search_response = requests.post(search_url, json=search_payload, timeout=30)
            if search_response.status_code == 200:
                search_result = search_response.json()
                nodes = search_result.get('nodes', [])
                print(f"Search found {len(nodes)} nodes for 'meridian agent'")
                for node in nodes:
                    print(f"  Node: {node.get('name', 'N/A')} - {node.get('summary', 'N/A')}")
        else:
            print(f"Error adding episode: {response.text}")
            
    except Exception as e:
        print(f"Error testing episode addition: {e}")

if __name__ == "__main__":
    print("=== Checking Existing Episodes ===")
    check_episodes()
    
    print("\n=== Testing Episode Addition ===")
    test_add_episode()